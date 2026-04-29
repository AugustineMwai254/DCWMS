"""Custom admin site configuration"""
from django.contrib.admin import AdminSite
from django.utils.translation import gettext_lazy as _

class DCWMSAdminSite(AdminSite):
    site_header = _("DCWMS Administration")
    site_title = _("DCWMS Admin Portal")
    index_title = _("Welcome to DCWMS Administration")
    site_url = "/"

    def get_app_list(self, request):
        """
        Return a sorted list of all the installed apps that have been
        registered in this site, with custom ordering.
        """
        app_list = super().get_app_list(request)

        # Define custom app ordering
        app_ordering = [
            'accounts',
            'warehouses',
            'bookings',
            'inventory',
            'receipts',
            'withdrawals',
            'reports',
        ]

        app_dict = {app['app_label']: app for app in app_list}

        # Reorder apps according to our custom ordering
        ordered_apps = []
        for app_label in app_ordering:
            if app_label in app_dict:
                ordered_apps.append(app_dict[app_label])

        # Add any remaining apps not in our custom ordering
        for app in app_list:
            if app not in ordered_apps:
                ordered_apps.append(app)

        return ordered_apps

# Create the admin site instance
admin_site = DCWMSAdminSite(name='dcwms_admin')