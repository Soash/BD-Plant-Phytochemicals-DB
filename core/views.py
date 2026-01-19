from django.shortcuts import render
from django.db.models import Q
from .models import Phytochemical

def bmppd(request):
    return render(request, 'core/bmppd.html')

def bmppd_result(request):
    query = request.GET.get('q', '').strip()
    results = []

    if query:
        qs = Phytochemical.objects.filter(
            Q(plant__scientific_name__icontains=query) |
            Q(plant__common_names__name__icontains=query) |
            Q(compound_name__icontains=query) |
            Q(cid__icontains=query)
        ).select_related('plant').distinct()

        # Prepare a list of dicts for the template
        for p in qs:
            # Combine all common names for this plant
            common_names = p.plant.common_names.all()
            common_name = ", ".join([c.name for c in common_names]) if common_names else ''
            
            results.append({
                'plant_name': p.plant.scientific_name,
                'common_name': common_name,
                'compound_name': p.compound_name,
                'cid': p.cid,
                'reference': p.reference,
            })

    context = {
        'query': query,
        'results': results
    }
    return render(request, 'core/bmppd_result.html', context)







def about(request):
    return render(request, 'core/about.html')

def acknowledgement(request):
    return render(request, 'core/acknowledgement.html')




