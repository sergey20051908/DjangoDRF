class OwnerMixin:
    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

    def get_queryset(self):
        user = self.request.user
        if user.groups.filter(name="moderators").exists():
            return super().get_queryset()
        return super().get_queryset().filter(owner=user)