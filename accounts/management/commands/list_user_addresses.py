from django.core.management.base import BaseCommand
from accounts.models import Customer

class Command(BaseCommand):
    help = 'List all user addresses'

    def add_arguments(self, parser):
        parser.add_argument(
            '--email',
            type=str,
            help='Filter by email address',
        )
        parser.add_argument(
            '--country',
            type=str,
            help='Filter by country',
        )
        parser.add_argument(
            '--format',
            type=str,
            choices=['table', 'json', 'csv'],
            default='table',
            help='Output format (table, json, csv)',
        )

    def handle(self, *args, **options):
        customers = Customer.objects.all()
        
        # Apply filters
        if options['email']:
            customers = customers.filter(email__icontains=options['email'])
        if options['country']:
            customers = customers.filter(country__icontains=options['country'])
        
        if not customers.exists():
            self.stdout.write(self.style.WARNING('No users found matching the criteria.'))
            return
        
        if options['format'] == 'json':
            self.output_json(customers)
        elif options['format'] == 'csv':
            self.output_csv(customers)
        else:
            self.output_table(customers)

    def output_table(self, customers):
        self.stdout.write(self.style.SUCCESS(f'\nFound {customers.count()} users:\n'))
        self.stdout.write('-' * 120)
        self.stdout.write(f"{'Email':<30} {'Name':<25} {'City':<15} {'State':<10} {'Country':<15} {'Postal Code':<10}")
        self.stdout.write('-' * 120)
        
        for customer in customers:
            name = f"{customer.first_name} {customer.last_name}".strip()
            self.stdout.write(
                f"{customer.email:<30} {name:<25} {customer.city or 'N/A':<15} "
                f"{customer.state or 'N/A':<10} {customer.country or 'N/A':<15} "
                f"{customer.postal_code or 'N/A':<10}"
            )
        
        self.stdout.write('-' * 120)

    def output_json(self, customers):
        import json
        data = []
        for customer in customers:
            data.append({
                'email': customer.email,
                'first_name': customer.first_name,
                'last_name': customer.last_name,
                'street_address': customer.street_address,
                'city': customer.city,
                'state': customer.state,
                'country': customer.country,
                'postal_code': customer.postal_code,
                'full_address': customer.get_full_address(),
            })
        self.stdout.write(json.dumps(data, indent=2))

    def output_csv(self, customers):
        import csv
        import io
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow(['Email', 'First Name', 'Last Name', 'Street Address', 'City', 'State', 'Country', 'Postal Code', 'Full Address'])
        
        # Write data
        for customer in customers:
            writer.writerow([
                customer.email,
                customer.first_name,
                customer.last_name,
                customer.street_address,
                customer.city,
                customer.state,
                customer.country,
                customer.postal_code,
                customer.get_full_address(),
            ])
        
        self.stdout.write(output.getvalue()) 