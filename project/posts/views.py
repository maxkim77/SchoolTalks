# posts > views.py

# Basic Django Modules
from django.shortcuts import get_object_or_404

# Rest Framework Modules
from rest_framework import generics, views, status, response, permissions
from rest_framework.permissions import IsAuthenticated

# Models
from .serializers import PostSerializer, CommentSerializer
from .models import Comment, Post, Like
from .permissions import IsOwnerOrReadOnly
from rest_framework.response import Response

class PostListView(generics.ListAPIView):
    queryset = Post.objects.order_by('-created_at')  # 최신순으로 정렬
    serializer_class = PostSerializer
    permission_classes = [permissions.IsAuthenticated]  # 인증된 사용자만 접근 가능


class PostDetailView(generics.RetrieveAPIView):
    queryset = Post.objects.all()
    serializer_class = PostSerializer
    
    def get(self,request, *args, **kwargs):
        instance = self.get_object()
        instance.increment_views()
        serializer = self.get_serializer(instance)
        return response.Response(serializer.data)


class PostCreateView(generics.CreateAPIView):
    queryset = Post.objects.all()
    serializer_class = PostSerializer
    permission_classes = [IsAuthenticated]  # 인증된 사용자만 접근 가능

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

class PostUpdateView(generics.UpdateAPIView):
    queryset = Post.objects.all()
    serializer_class = PostSerializer
    # permission_classes = [IsAuthenticated, IsOwnerOrReadOnly]  
    
    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(author=self.request.user)
        return Response(serializer.data)

# posts > views.py

# ... (이전 코드)

class PostDeleteView(generics.DestroyAPIView):
    queryset = Post.objects.all()
    serializer_class = PostSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrReadOnly]  # 인증된 사용자만 접근 가능하며, 작성자만 삭제 가능

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.author == request.user:
            instance.delete()
            return Response(status=status.HTTP_200_OK)  # 상태 코드를 200으로 변경
        else:
            return Response({'detail': '권한이 없습니다.'}, status=status.HTTP_403_FORBIDDEN)


class CommentCreateView(generics.CreateAPIView):
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)


class CommentListView(generics.ListAPIView):
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer

    def get_queryset(self):
        return self.queryset.filter(post_id=self.kwargs['post_id'])


class LikeView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, post_id):
        post = get_object_or_404(Post, id=post_id)
        like, created = Like.objects.get_or_create(post=post, user=request.user)

        # 좋아요를 검색한 후 좋아요가 없으면 생성(like 생성된 객체, created가 생성 여부 판단)
        # created == True : 좋아요가 클릭이 안되어 있어서 새로 생성했다.
        # created == False : 좋아요가 클릭이 되어서 생성하지 못했다.

        if not created:
            # 이미 좋아요가 존재하는 경우, 409 Conflict 반환
            return response.Response(status=status.HTTP_409_CONFLICT)

        # 좋아요가 생성되었으면 201 응답
        return response.Response(status=status.HTTP_201_CREATED)

    def delete(self, request, post_id):
        post = get_object_or_404(Post, id=post_id) # 게시물이 존재하지 않으면 404 에러
        like = get_object_or_404(Like, post=post, user=request.user) # 좋아요가 존재하지 않으면 404 에러
        like.delete()
        return response.Response(status=status.HTTP_204_NO_CONTENT) # 좋아요가 삭제되었으면 204 응답
