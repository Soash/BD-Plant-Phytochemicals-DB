import csv
import os
import logging
from django.core.management.base import BaseCommand
from django.conf import settings
from core.models import Plant, CommonName, Phytochemical

DATA_DIR = os.path.join(settings.BASE_DIR, 'data')
DETAILED_LOG_FILE = os.path.join(settings.BASE_DIR, 'phytochemical_import.log')
SUMMARY_LOG_FILE = os.path.join(settings.BASE_DIR, 'phytochemical_summary.log')


def clean_text(val):
    if not val:
        return ''
    return val.replace('\xa0', '').strip()


class Command(BaseCommand):
    help = "Import phytochemical CSV files with biologically correct accounting"

    def handle(self, *args, **kwargs):

        # ---------- LOGGERS ----------
        logger = logging.getLogger('phytochemical_import')
        logger.setLevel(logging.INFO)
        logger.handlers.clear()

        fh = logging.FileHandler(DETAILED_LOG_FILE, mode='w', encoding='utf-8')
        fh.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        logger.addHandler(fh)
        logger.addHandler(logging.StreamHandler())

        summary_logger = logging.getLogger('phytochemical_summary')
        summary_logger.setLevel(logging.INFO)
        summary_logger.handlers.clear()

        sh = logging.FileHandler(SUMMARY_LOG_FILE, mode='w', encoding='utf-8')
        sh.setFormatter(logging.Formatter('%(message)s'))
        summary_logger.addHandler(sh)

        # ---------- GLOBAL TOTALS ----------
        plants_created = 0
        common_names_created = 0
        phytochem_created_total = 0
        phytochem_existing_total = 0

        files = sorted(f for f in os.listdir(DATA_DIR) if f.lower().endswith('.csv'))
        if not files:
            logger.warning("No CSV files found.")
            return

        # ---------- FILE LOOP ----------
        for filename in files:
            logger.info(f"\nProcessing file: {filename}")
            file_path = os.path.join(DATA_DIR, filename)

            current_plant = None

            total_rows = 0
            rows_with_compound = 0
            rows_common_only = 0
            phytochem_created = 0
            phytochem_existing = 0
            rows_without_compound = []

            try:
                with open(file_path, encoding='utf-8-sig', newline='') as f:
                    reader = csv.DictReader(f)
                    rows = [
                        row for row in reader
                        if any(v and v.strip() for v in row.values())
                    ]
            except UnicodeDecodeError:
                with open(file_path, encoding='latin1', newline='') as f:
                    reader = csv.DictReader(f)
                    rows = [
                        row for row in reader
                        if any(v and v.strip() for v in row.values())
                    ]

            total_rows = len(rows)
            if total_rows == 0:
                summary_logger.info(f"{filename}: EMPTY FILE")
                continue

            # ---------- ROW LOOP ----------
            for i, row in enumerate(rows, start=1):
                row = {k.strip().lower(): v for k, v in row.items()}

                plant_name = clean_text(row.get('plant name'))
                common_name = clean_text(row.get('common name'))
                compound = clean_text(row.get('phytochemicals'))
                cid = clean_text(row.get('cid'))
                reference = clean_text(row.get('reference'))

                if plant_name:
                    current_plant, created = Plant.objects.get_or_create(
                        scientific_name=plant_name
                    )
                    if created:
                        plants_created += 1
                        logger.info(f"Created Plant: {plant_name}")

                if not current_plant:
                    continue

                if common_name:
                    cn, created = CommonName.objects.get_or_create(
                        plant=current_plant,
                        name=common_name
                    )
                    if created:
                        common_names_created += 1
                        logger.info(f"Row {i}: Added Common Name: {common_name}")

                if not compound:
                    rows_common_only += 1
                    rows_without_compound.append(str(i))
                    continue

                rows_with_compound += 1

                try:
                    obj, created = Phytochemical.objects.get_or_create(
                        plant=current_plant,
                        compound_name=compound,
                        cid=cid,
                        defaults={'reference': reference}
                    )

                    if created:
                        phytochem_created += 1
                        phytochem_created_total += 1
                        logger.info(f"Row {i}: Added Phytochemical: {compound}")
                    else:
                        phytochem_existing += 1
                        phytochem_existing_total += 1
                        if not obj.reference and reference:
                            obj.reference = reference
                            obj.save()

                except Exception as e:
                    logger.error(f"Row {i}: DB error for {compound}: {e}")

            # ---------- CONDITIONAL SUMMARY ----------
            summary_parts = [
                f"{filename}: Total rows={total_rows}",
                f"Rows with phytochemicals={rows_with_compound}",
                f"Unique phytochemicals CREATED={phytochem_created}",
                f"Phytochemicals already existed={phytochem_existing}",
            ]

            # Log rows without compounds ONLY if meaningful
            if (
                rows_without_compound
                and rows_with_compound != phytochem_created
            ):
                summary_parts.append(
                    f"Rows without compounds={', '.join(rows_without_compound)}"
                )

            summary_logger.info(", ".join(summary_parts))

        # ---------- FINAL TOTAL ----------
        logger.info("\nIMPORT COMPLETE")
        logger.info(f"Plants created: {plants_created}")
        logger.info(f"Common names created: {common_names_created}")
        logger.info(f"Phytochemicals created: {phytochem_created_total}")
        logger.info(f"Phytochemicals already existed: {phytochem_existing_total}")

        summary_logger.info("\n=== FINAL TOTALS ===")
        summary_logger.info(f"Plants created: {plants_created}")
        summary_logger.info(f"Common names created: {common_names_created}")
        summary_logger.info(f"Phytochemicals created: {phytochem_created_total}")
        summary_logger.info(f"Phytochemicals already existed: {phytochem_existing_total}")
