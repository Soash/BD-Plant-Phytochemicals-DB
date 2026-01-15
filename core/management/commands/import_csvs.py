import csv
import os
from django.core.management.base import BaseCommand
from django.conf import settings
from core.models import Plant, CommonName, Phytochemical

DATA_DIR = os.path.join(settings.BASE_DIR, 'data')


def clean_text(val):
    """Clean string: remove non-breaking spaces, trim, return empty string if None."""
    if not val:
        return ''
    return val.replace('\xa0', '').strip()


class Command(BaseCommand):
    help = "Import all phytochemical CSV files into the database (case-insensitive headers)"

    def handle(self, *args, **kwargs):
        total_phytochemicals = 0
        total_plants = 0
        total_common_names = 0

        files = [f for f in os.listdir(DATA_DIR) if f.lower().endswith('.csv')]
        if not files:
            self.stdout.write(self.style.WARNING("No CSV files found in 'data/' folder."))
            return

        for filename in files:
            file_path = os.path.join(DATA_DIR, filename)
            self.stdout.write(f"\nProcessing file: {filename}")

            current_plant = None  # Reset per CSV

            # Try UTF-8 first, fallback to Latin-1
            try:
                f = open(file_path, encoding='utf-8-sig', newline='')
                reader = csv.DictReader(f)
                rows = list(reader)
                f.close()
            except UnicodeDecodeError:
                self.stdout.write(f"UTF-8 decode failed for {filename}, trying latin1...")
                f = open(file_path, encoding='latin1', newline='')
                reader = csv.DictReader(f)
                rows = list(reader)
                f.close()

            if not rows:
                self.stdout.write(self.style.WARNING(f"No rows found in {filename}, skipping."))
                continue

            for i, row in enumerate(rows, start=1):
                # Make header lookup case-insensitive
                row = {k.strip().lower(): v for k, v in row.items()}

                plant_name = clean_text(row.get('plant name'))
                common_name = clean_text(row.get('common name'))
                compound = clean_text(row.get('phytochemicals'))
                cid = clean_text(row.get('cid'))
                reference = clean_text(row.get('reference'))

                # Skip rows without compound
                if not compound:
                    self.stdout.write(f"Row {i}: Missing compound, skipping.")
                    continue

                # Update current plant if plant_name exists in this row
                if plant_name:
                    current_plant, created = Plant.objects.get_or_create(
                        scientific_name=plant_name
                    )
                    if created:
                        total_plants += 1
                        self.stdout.write(f"Created new Plant: {plant_name}")

                # Skip row if no plant available yet
                if not current_plant:
                    self.stdout.write(f"Row {i}: No plant info, skipping.")
                    continue

                # Create CommonName if present
                if common_name:
                    cn_obj, created = CommonName.objects.get_or_create(
                        plant=current_plant,
                        name=common_name
                    )
                    if created:
                        total_common_names += 1
                        self.stdout.write(f"Row {i}: Added Common Name: {common_name}")

                # Create Phytochemical (UNIQUE-safe)
                try:
                    obj, created = Phytochemical.objects.get_or_create(
                        plant=current_plant,
                        compound_name=compound,
                        cid=cid,
                        defaults={'reference': reference}
                    )
                    if not created and not obj.reference and reference:
                        obj.reference = reference
                        obj.save()
                        self.stdout.write(f"Row {i}: Updated reference for {compound}")
                    total_phytochemicals += 1
                    if created:
                        self.stdout.write(f"Row {i}: Added Phytochemical: {compound}")
                except Exception as e:
                    self.stdout.write(self.style.ERROR(
                        f"Row {i}: Failed to add {compound} - {e}"
                    ))

        self.stdout.write(self.style.SUCCESS(
            f"\nImport complete: {total_plants} plants, "
            f"{total_common_names} common names, "
            f"{total_phytochemicals} phytochemicals"
        ))


