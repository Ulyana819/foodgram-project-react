from django.contrib.admin import ModelAdmin, TabularInline, register

from recipes.models import (Favorite, Ingredient, Recipe, RecipeIngredient,
                            ShoppingCart, Tag)


class RecipeIngredientInline(TabularInline):
    model = RecipeIngredient
    min_num = 1


@register(Ingredient)
class IngredientAdmin(ModelAdmin):
    list_display = ('name', 'measurement_unit')
    search_fields = ('name',)


@register(Tag)
class TagAdmin(ModelAdmin):
    list_display = ('name', 'color', 'slug')


@register(Recipe)
class RecipeAdmin(ModelAdmin):
    inlines = [RecipeIngredientInline, ]
    list_display = ('name', 'author', 'pub_date', 'display_tags', 'favorite')
    list_filter = ('name', 'author')
    search_fields = ('name',)
    readonly_fields = ('favorite',)
    fields = ('image',
              ('name', 'author'),
              'text',
              ('tags', 'cooking_time'),
              'favorite')
    filter_horizontal = ('tag')

    def display_tags(self, obj):
        return ', '.join([tag.name for tag in obj.tags.all()])
    display_tags.short_description = 'Теги'


@register(RecipeIngredient)
class RecipeIngredientAdmin(ModelAdmin):
    list_display = ('recipe', 'ingredient', 'amount')


@register(Favorite)
class FavoriteAdmin(ModelAdmin):
    list_display = ('recipe', 'user')


@register(ShoppingCart)
class ShoppingCartAdmin(ModelAdmin):
    list_display = ('recipe', 'user')
