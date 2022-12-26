from api.serializers.users import FollowSerializer, UsersSerializer
from django.shortcuts import get_object_or_404
from djoser.views import UserViewSet
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import (IsAuthenticated,
                                        IsAuthenticatedOrReadOnly)
from rest_framework.response import Response
from users.models import User


class UsersViewSet(UserViewSet):
    queryset = User.objects.all()
    serializer_class = UsersSerializer
    permission_classes = (IsAuthenticatedOrReadOnly,)

    def get_permissions(self):
        if self.action == 'me':
            self.permission_classes = (IsAuthenticated,)
        return super().get_permissions()

    @action(detail=True, methods=['post'])
    def subscribe(self, request, id):
        user = request.user
        author = get_object_or_404(User, id=id)
        if subscrsiption.exists():
            return Response({'error': 'Вы уже подписаны'},
                            status=status.HTTP_400_BAD_REQUEST)
        if user == author:
            return Response({'error': 'Невозможно подписаться на себя'},
                            status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['delete'])
    def subscription_delete(self, request):
        if subscribe.exists():
            subscribe.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
            return Response({'error': 'Вы не подписаны на этого пользователя'},
                            status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, permission_classes=[IsAuthenticated])
    def subscriptions(self, request):
        user = request.user
        follows = User.objects.filter(following__user=user)
        page = self.paginate_queryset(follows)
        serializer = FollowSerializer(
            page, many=True,
            context={'request': request})
        return self.get_paginated_response(serializer.data)
