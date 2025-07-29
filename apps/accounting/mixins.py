import pandas as pd
from django.http import HttpResponse
from django.template.loader import render_to_string
from weasyprint import HTML


class ExportMixin:
    export_filename = "exported_data"

    def export_to_excel(self, queryset):
        df = pd.DataFrame(list(queryset.values()))
        response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = f'attachment; filename={self.export_filename}.xlsx'
        with pd.ExcelWriter(response, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Data')
        return response

    def export_to_pdf(self, queryset, template_name, context_name):
        html_string = render_to_string(template_name, {context_name: queryset})
        html = HTML(string=html_string)
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename={self.export_filename}.pdf'
        html.write_pdf(response)
        return response

    def get(self, request, *args, **kwargs):
        export_format = request.GET.get('export', None)
        queryset = self.get_queryset()

        if export_format == 'excel':
            return self.export_to_excel(queryset)
        elif export_format == 'pdf':
            return self.export_to_pdf(queryset, self.template_name, self.context_object_name)

        return super().get(request, *args, **kwargs)
