import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Count, Q
from django.http import JsonResponse

from .models import Client, Credit, PredictionRisque
from .forms import ClientForm, EvaluationForm, CreditForm
from .ml_model import predict_risk, montant_maximum_accordable


def _get_contexte_credit(client):
    """
    Analyse l'historique de crédit du client et retourne :
    - a_credit_en_cours    : bool — bloquant absolu
    - a_antecedent_defaut  : bool — bloquant absolu
    - credits_en_cours     : queryset
    - nb_credits_soldes    : int (historique valide)
    - nb_retards_total     : int (sur crédits soldés uniquement)
    """
    credits_en_cours = client.credits.filter(statut='en_cours')
    credits_defaut = client.credits.filter(statut='defaut')
    credits_soldes = client.credits.filter(statut='solde')

    nb_retards_total = sum(c.nb_retards for c in credits_soldes)

    return {
        'a_credit_en_cours': credits_en_cours.exists(),
        'a_antecedent_defaut': credits_defaut.exists(),
        'credits_en_cours': credits_en_cours,
        'nb_credits_soldes': credits_soldes.count(),
        'nb_retards_total': nb_retards_total,
    }


def dashboard(request):
    total_clients = Client.objects.count()
    total_credits = Credit.objects.count()
    total_predictions = PredictionRisque.objects.count()

    credits_defaut = Credit.objects.filter(statut='defaut').count()
    taux_defaut = round(credits_defaut / total_credits * 100, 1) if total_credits else 0

    risque_faible = PredictionRisque.objects.filter(niveau_risque='faible').count()
    risque_moyen = PredictionRisque.objects.filter(niveau_risque='moyen').count()
    risque_eleve = PredictionRisque.objects.filter(niveau_risque='eleve').count()
    risque_refuse = PredictionRisque.objects.filter(niveau_risque='refuse').count()

    derniers_clients = Client.objects.order_by('-date_creation')[:5]
    dernieres_predictions = PredictionRisque.objects.select_related('client').order_by('-date_prediction')[:5]

    context = {
        'total_clients': total_clients,
        'total_credits': total_credits,
        'total_predictions': total_predictions,
        'taux_defaut': taux_defaut,
        'credits_defaut': credits_defaut,
        'risque_faible': risque_faible,
        'risque_moyen': risque_moyen,
        'risque_eleve': risque_eleve,
        'risque_refuse': risque_refuse,
        'derniers_clients': derniers_clients,
        'dernieres_predictions': dernieres_predictions,
    }
    return render(request, 'risk/dashboard.html', context)


def client_list(request):
    q = request.GET.get('q', '')
    clients = Client.objects.annotate(
        nb_credits=Count('credits'),
        nb_predictions=Count('predictions')
    ).order_by('-date_creation')
    if q:
        clients = clients.filter(
            Q(nom__icontains=q) | Q(prenom__icontains=q) |
            Q(ville__icontains=q) | Q(telephone__icontains=q)
        )
    return render(request, 'risk/client_list.html', {'clients': clients, 'q': q})


def client_create(request):
    if request.method == 'POST':
        form = ClientForm(request.POST)
        if form.is_valid():
            client = form.save()
            messages.success(request, f"Client {client.prenom} {client.nom} créé avec succès.")
            return redirect('client_detail', pk=client.pk)
    else:
        form = ClientForm()
    return render(request, 'risk/client_form.html', {'form': form, 'action': 'Ajouter'})


def client_detail(request, pk):
    client = get_object_or_404(Client, pk=pk)
    credits = client.credits.order_by('-date_debut')
    predictions = client.predictions.order_by('-date_prediction')
    ctx = _get_contexte_credit(client)

    # Pré-remplissage intelligent du formulaire
    eval_form = EvaluationForm(initial={
        'client_id': client.pk,
        'nb_credits_anterieurs': ctx['nb_credits_soldes'],
        'nb_retards_anterieurs': ctx['nb_retards_total'],
    })
    credit_form = CreditForm()

    # Calcul du montant max pour chaque durée (affiché en info)
    montants_max = {
        str(d): int(montant_maximum_accordable(client.revenu_mensuel, d))
        for d in [6, 12, 18, 24, 36]
    }

    return render(request, 'risk/client_detail.html', {
        'client': client,
        'credits': credits,
        'predictions': predictions,
        'eval_form': eval_form,
        'credit_form': credit_form,
        'ctx_credit': ctx,
        'montants_max': json.dumps(montants_max),
    })


def client_edit(request, pk):
    client = get_object_or_404(Client, pk=pk)
    if request.method == 'POST':
        form = ClientForm(request.POST, instance=client)
        if form.is_valid():
            form.save()
            messages.success(request, "Client mis à jour.")
            return redirect('client_detail', pk=pk)
    else:
        form = ClientForm(instance=client)
    return render(request, 'risk/client_form.html', {
        'form': form, 'client': client, 'action': 'Modifier'
    })


def evaluer_client(request, pk):
    """Lance l'analyse (règles métier + ML) et sauvegarde la prédiction."""
    client = get_object_or_404(Client, pk=pk)
    if request.method != 'POST':
        return redirect('client_detail', pk=pk)

    form = EvaluationForm(request.POST)
    if not form.is_valid():
        messages.error(request, "Formulaire invalide. Vérifiez les données.")
        return redirect('client_detail', pk=pk)

    data = form.cleaned_data
    ctx = _get_contexte_credit(client)

    result = predict_risk(
        age=client.age,
        revenu_mensuel=client.revenu_mensuel,
        nb_credits_anterieurs=ctx['nb_credits_soldes'],
        nb_retards_anterieurs=ctx['nb_retards_total'],
        montant_demande=data['montant_demande'],
        secteur_activite=client.secteur_activite,
        duree_mois=int(data['duree_mois']),
        a_credit_en_cours=ctx['a_credit_en_cours'],
        a_antecedent_defaut=ctx['a_antecedent_defaut'],
    )

    prediction = PredictionRisque.objects.create(
        client=client,
        eligible=result['eligible'],
        score_fiabilite=result['score_fiabilite'],
        niveau_risque=result['niveau_risque'],
        probabilite_defaut=result['probabilite_defaut'],
        recommandation=result['recommandation'],
        blocages_json=json.dumps(result['blocages'], ensure_ascii=False),
        montant_demande=data['montant_demande'],
        duree_mois_input=int(data['duree_mois']),
        mensualite=result['mensualite'],
        taux_effort=result['taux_effort'],
        ratio_endettement=result['ratio_endettement'],
        montant_max_accordable=result['montant_max_accordable'],
        age_input=client.age,
        revenu_input=client.revenu_mensuel,
        nb_credits_anterieurs=ctx['nb_credits_soldes'],
        nb_retards_anterieurs=ctx['nb_retards_total'],
    )

    return redirect('resultat_prediction', pk=prediction.pk)


def resultat_prediction(request, pk):
    prediction = get_object_or_404(PredictionRisque, pk=pk)
    blocages = json.loads(prediction.blocages_json)
    return render(request, 'risk/resultat.html', {
        'prediction': prediction,
        'blocages': blocages,
    })


def add_credit(request, pk):
    client = get_object_or_404(Client, pk=pk)
    if request.method == 'POST':
        # Vérification : pas de doublon en cours
        if client.credits.filter(statut='en_cours').exists():
            messages.error(request, "Impossible d'ajouter un crédit : ce client a déjà un crédit en cours.")
            return redirect('client_detail', pk=pk)
        form = CreditForm(request.POST)
        if form.is_valid():
            credit = form.save(commit=False)
            credit.client = client
            credit.save()
            messages.success(request, "Crédit enregistré.")
    return redirect('client_detail', pk=pk)


def api_stats(request):
    par_secteur = (
        Client.objects.values('secteur_activite')
        .annotate(total=Count('id')).order_by('-total')
    )
    par_risque = {
        'faible': PredictionRisque.objects.filter(niveau_risque='faible').count(),
        'moyen': PredictionRisque.objects.filter(niveau_risque='moyen').count(),
        'eleve': PredictionRisque.objects.filter(niveau_risque='eleve').count(),
        'refuse': PredictionRisque.objects.filter(niveau_risque='refuse').count(),
    }
    return JsonResponse({'par_secteur': list(par_secteur), 'par_risque': par_risque})
