from django.core.management.base import BaseCommand
from suppliers.models import SupplierInvitation
from django.db.models import Count
from django.utils import timezone

class Command(BaseCommand):
    help = 'Clean up duplicate supplier invitations'

    def handle(self, *args, **options):
        # Find all duplicate active invitations
        duplicates = (
            SupplierInvitation.objects
            .values('email', 'supplier')
            .annotate(count=Count('id'))
            .filter(count__gt=1)
        )

        for duplicate in duplicates:
            invitations = SupplierInvitation.objects.filter(
                email=duplicate['email'],
                supplier_id=duplicate['supplier']
            ).order_by('-created_at')
            
            # Keep the most recent one
            latest = invitations.first()
            
            # Mark all others as used
            invitations.exclude(id=latest.id).update(
                is_used=True,
                expires_at=timezone.now()
            )
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'Cleaned up {invitations.count() - 1} duplicate invitations for {duplicate["email"]}'
                )
            ) 