from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from api.filters import IngredientFilter, RecipeFilter
from api.paginations import LimitPagination
from api.permissions import IsAuthorOrReadOnly
from api.serializers.recipes import (FavoriteSerializer, IngredientSerializer,
                                     RecipeSerializer, ShoppingCartSerializer,
                                     TagSerializer)
from recipes.models import Ingredient, Recipe, RecipeIngredient, Tag


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    filter_backends = (DjangoFilterBackend,)
    filterset_class = IngredientFilter
    permission_classes = (AllowAny,)
    pagination_class = None


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = (AllowAny,)
    pagination_class = None


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    serializer_class = RecipeSerializer
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter
    permission_classes = (IsAuthorOrReadOnly,)
    pagination_class = LimitPagination

    def _action_post(self, pk, serializer_class):
        user = self.request.user
        serializer = serializer_class(
            data={'user': user.id, 'recipe': pk},
            context={'request': self.request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def _action_delete(self, pk, serializer_class):
        user = self.request.user
        recipe = get_object_or_404(Recipe, pk=pk)
        object = serializer_class.Meta.model.objects.filter(
            user=user, recipe=recipe
        )
        if object.exists():
            object.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response({'error': 'Этого рецепта нет в списке'},
                        status=status.HTTP_400_BAD_REQUEST)

    @action(methods=['POST'], detail=True)
    def favorite(self, request, pk):
        return self._action_post(pk, FavoriteSerializer)

    @favorite.mapping.delete
    def favorite_delete(self, request, pk):
        return self._action_delete(pk, FavoriteSerializer)

    @action(methods=['POST'], detail=True)
    def shopping_cart(self, request, pk):
        return self._action_post(pk, ShoppingCartSerializer)

    @shopping_cart.mapping.delete
    def shopping_cart_delete(self, request, pk):
        return self._action_delete(pk, ShoppingCartSerializer)

    @action(detail=False)
    def download_shopping_cart(self, request):
        user = self.request.user
        ingredients = RecipeIngredient.objects.filter(
            recipe__shoppingcart__user=user
        ).prefetch_related(
            'recipe_set', 'ingredientinrecipe_set'
        ).annotate(
            ingredient_amount=Sum('ingredientinrecipe__amount')
        ).values_list('name', 'measurement_unit', 'ingredient_amount')
        pdfmetrics.registerFont(
            TTFont(
                'SF-Pro',
                Path(settings.DATA_ROOT, 'fonts/SF-Pro.ttf'), 'UTF-8'
            )
        )
        response = HttpResponse(content_type='application/pdf')
        filename = 'shopping_list.pdf'
        response['Content-Disposition'] = (
            'attachment; filename="%s"' % filename
        )
        file = canvas.Canvas(response, pagesize=A4)
        file.setFont('SF-Pro', size=24)
        file.drawString(200, 800, 'Список покупок')
        file.setFont('SF-Pro', size=16)
        height = 750
        for index, (name, unit, amount) in enumerate(ingredients, 1):
            file.drawString(
                75, height, '%d. %s (%s) - %s' % (
                    index, name, unit, amount
                )
            )
            if height <= 50:
                height = 800
                file.showPage()
                file.setFont('SF-Pro', size=16)
            height -= 25
        file.showPage()
        file.save()
        return response
