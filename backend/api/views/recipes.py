from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from reportlab.pdfbase import pdfmetrics, ttfonts
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
        user = request.user
        cart = user.purchase_set.all()
        buying_list = {}
        for item in cart:
            recipe = item.recipe
            ingredients_in_recipe = IngredientInRecipe.objects.filter(
                recipe=recipe
            )
            for item in ingredients_in_recipe:
                amount = item.amount
                name = item.ingredient.name
                measurement_unit = item.ingredient.measurement_unit
                if name not in buying_list:
                    buying_list[name] = {
                        'amount': amount,
                        'measurement_unit': measurement_unit
                    }
                else:
                    buying_list[name]['amount'] = (
                        buying_list[name]['amount'] + amount
                    )
        shopping_list = []
        for item in buying_list:
            shopping_list.append(
                f'{item} - {buying_list[item]["amount"]}, '
                f'{buying_list[item]["measurement_unit"]}\n'
            )
        response = HttpResponse(shopping_list, 'Content-Type: text/plain')
        response['Content-Disposition'] = (
            'attachment;' 'filename="shopping_list.txt"'
        )
        return response
