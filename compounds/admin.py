from django.contrib import admin

from .models import Compound, CompoundElement, Element


class CompoundElementInline(admin.TabularInline):
    model = CompoundElement
    extra = 1
    autocomplete_fields = ['element']


@admin.register(Element)
class ElementAdmin(admin.ModelAdmin):
    list_display = ('atomic_number', 'symbol', 'name', 'weight')
    search_fields = ('name', 'symbol')
    ordering = ('atomic_number',)


@admin.register(Compound)
class CompoundAdmin(admin.ModelAdmin):
    list_display = ('name', 'formula', 'weight', 'acid_base_type', 'risk_level')
    list_filter = ('acid_base_type', 'risk_level')
    search_fields = ('name', 'formula', 'description', 'usage')
    ordering = ('name',)
    inlines = [CompoundElementInline]


@admin.register(CompoundElement)
class CompoundElementAdmin(admin.ModelAdmin):
    list_display = ('compound', 'element', 'element_count')
    autocomplete_fields = ('compound', 'element')
    search_fields = ('compound__name', 'compound__formula', 'element__name', 'element__symbol')
