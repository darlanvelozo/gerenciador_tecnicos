from django.shortcuts import render
from .models import Tecnico

def listar_tecnicos(request):
    tecnicos = Tecnico.objects.all()
    return render(request, 'tecnicos/listar_tecnicos.html', {'tecnicos': tecnicos})