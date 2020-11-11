from django.http import HttpResponse
from django.shortcuts import render
from . import demo

# Create your views here.

def test(request):
    demo.test()
    return HttpResponse("ok")