from django.http import HttpResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt

from . import demo

# Create your views here.

@csrf_exempt
def test(request):
    demo.test()
    return HttpResponse("ok")