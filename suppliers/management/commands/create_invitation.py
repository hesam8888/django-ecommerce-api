from django.core.management.base import BaseCommand
from suppliers.models import SupplierInvitation, User

class Command(BaseCommand):
    help = 'Create a supplier invitation'

    def add_arguments(self, parser):
        parser.add_argument('email', type=str, help='Supplier email address')
        parser.add_argument('store_name', type=str, help='Store name')
        parser.add_argument('owner_name', type=str, help='Owner full name')
        parser.add_argument('--phone', type=str, default='', help='Phone number')
        parser.add_argument('--address', type=str, default='', help='Store address')
        parser.add_argument('--admin-email', type=str, help='Admin email who is creating the invitation')

    def handle(self, *args, **options):
        email = options['email']
        store_name = options['store_name']
        owner_name = options['owner_name']
        phone = options['phone']
        address = options['address']
        admin_email = options['admin_email']

        # Get admin user
        if admin_email:
            try:
                admin_user = User.objects.get(email=admin_email)
            except User.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f'Admin user with email {admin_email} not found.')
                )
                return
        else:
            # Get first staff user
            admin_user = User.objects.filter(is_staff=True).first()
            if not admin_user:
                self.stdout.write(
                    self.style.ERROR('No admin user found. Please specify --admin-email.')
                )
                return

        # Create invitation
        try:
            invitation = SupplierInvitation.objects.create(
                email=email,
                store_name=store_name,
                owner_name=owner_name,
                phone=phone,
                address=address,
                created_by=admin_user
            )

            self.stdout.write(
                self.style.SUCCESS(f'Invitation created successfully!')
            )
            self.stdout.write(f'Token: {invitation.token}')
            from django.conf import settings
            from django.urls import reverse
            registration_url = reverse('suppliers:register', kwargs={'token': invitation.token})
            full_url = f"{settings.SITE_URL}{registration_url}"
            self.stdout.write(f'Registration URL: {full_url}')
            self.stdout.write(f'Expires: {invitation.expires_at}')
            
            if invitation.is_sent:
                self.stdout.write(
                    self.style.SUCCESS('Invitation email sent successfully!')
                )
            else:
                self.stdout.write(
                    self.style.WARNING('Invitation email was not sent. Check your email configuration.')
                )

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error creating invitation: {e}')
            ) 