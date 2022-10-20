from django.views.generic.base import TemplateView


class AboutStaticPage(TemplateView):
    template_name = 'about/about.html'


class TechStaticPage(TemplateView):
    template_name = 'about/tech.html'
