from django.contrib import admin
from .models import Plant, CommonName, Phytochemical


# --- Inline Admins ---
class CommonNameInline(admin.TabularInline):
    model = CommonName
    extra = 1  # Number of empty forms to display
    autocomplete_fields = ['plant']


class PhytochemicalInline(admin.TabularInline):
    model = Phytochemical
    extra = 1
    autocomplete_fields = ['plant']


# --- Plant Admin ---
@admin.register(Plant)
class PlantAdmin(admin.ModelAdmin):
    search_fields = ('scientific_name',)
    list_display = ('scientific_name', 'common_names_list', 'phytochemicals_count')
    inlines = [CommonNameInline, PhytochemicalInline]

    def common_names_list(self, obj):
        return ", ".join([cn.name for cn in obj.common_names.all()])
    common_names_list.short_description = "Common Names"

    def phytochemicals_count(self, obj):
        return obj.phytochemicals.count()
    phytochemicals_count.short_description = "Number of Phytochemicals"


# --- Common Name Admin ---
@admin.register(CommonName)
class CommonNameAdmin(admin.ModelAdmin):
    search_fields = ('name', 'plant__scientific_name')
    list_display = ('name', 'plant')
    list_filter = ('plant',)


# --- Phytochemical Admin ---
@admin.register(Phytochemical)
class PhytochemicalAdmin(admin.ModelAdmin):
    search_fields = ('compound_name', 'cid', 'plant__scientific_name')
    list_display = ('compound_name', 'plant', 'cid', 'reference')
    list_filter = ('plant',)
    autocomplete_fields = ['plant']





# admin.py
from django.contrib import admin, messages
from .models import CSVUpload, Plant, CommonName, Phytochemical

@admin.register(CSVUpload)
class CSVUploadAdmin(admin.ModelAdmin):
    list_display = ('file', 'uploaded_at')
    readonly_fields = ('uploaded_at',)

    def save_model(self, request, obj, form, change):
        """
        Override save to import CSV automatically and show success message.
        """
        super().save_model(request, obj, form, change)  # Save first

        # Import CSV and get totals
        totals = obj.import_csv()

        # Display success message in admin
        messages.success(
            request,
            f"CSV import complete: "
            f"{totals['plants']} plant(s), "
            f"{totals['common_names']} common name(s), "
            f"{totals['phytochemicals']} phytochemical(s) imported."
        )


