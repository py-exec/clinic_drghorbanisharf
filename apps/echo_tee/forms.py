# apps/echo_tee/forms.py

from django import forms
from .models import TEEEchoReport


class TEEEchoReportForm(forms.ModelForm):
    class Meta:
        model = TEEEchoReport
        fields = [
            'patient',
            'prescription',
            'exam_datetime',
            'sedation_used',
            'patient_cooperation',
            'visualization_quality',
            'la_appendage_status',
            'interatrial_septum',
            'valvular_findings',
            'presence_of_clot',
            'pericardial_effusion',
            'findings',
            'doctor_opinion',
            'recommendation',
            'echo_file',
            # 'created_by' and 'reception_service' will be set in the view
        ]
        # Adding widgets for better UI/UX if needed
        widgets = {
            'exam_datetime': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'findings': forms.Textarea(attrs={'rows': 4}),
            'doctor_opinion': forms.Textarea(attrs={'rows': 4}),
            'recommendation': forms.Textarea(attrs={'rows': 4}),
            'la_appendage_status': forms.Textarea(attrs={'rows': 3}),
            'interatrial_septum': forms.Textarea(attrs={'rows': 3}),
            'valvular_findings': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make patient and prescription fields read-only or hidden if set via URL/view
        # if 'patient' in self.fields:
        #     self.fields['patient'].widget = forms.HiddenInput() # Or forms.Select(attrs={'readonly': 'readonly'})
        #     # self.fields['patient'].required = False # If it's set programmatically
        # if 'prescription' in self.fields:
        #     # You might want to filter prescription choices based on the patient in the view
        #     pass

        # Add Bootstrap form-control class to all fields for styling
        for field_name, field in self.fields.items():
            if isinstance(field.widget,
                          (forms.TextInput, forms.Textarea, forms.Select, forms.DateInput, forms.DateTimeInput,
                           forms.NumberInput, forms.FileInput)):
                if 'class' in field.widget.attrs:
                    field.widget.attrs['class'] += ' form-control'
                else:
                    field.widget.attrs['class'] = 'form-control'
            # Handle CheckboxInput separately as it doesn't usually use form-control
            elif isinstance(field.widget, forms.CheckboxInput):
                if 'class' in field.widget.attrs:
                    field.widget.attrs['class'] += ' form-check-input'
                else:
                    field.widget.attrs['class'] = 'form-check-input'

            # Remove required attribute from reception_service if it's implicitly set
            if field_name == 'patient':
                # This field should be set in the view, so it's not directly edited by the user in the form
                # But it's needed for model validation.
                # If you make it hidden, it will still pass the value from the initial
                self.fields['patient'].widget = forms.Select(
                    attrs={'disabled': 'disabled'})  # Make it disabled to show but not editable
                self.fields['patient'].required = False  # Not required in form as it's set by view
            if field_name == 'prescription':
                self.fields['prescription'].empty_label = "--- انتخاب نسخه ---"