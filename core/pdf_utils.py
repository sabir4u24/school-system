from django.http import HttpResponse
from django.template.loader import get_template
from weasyprint import HTML
import io

def render_to_pdf(template_src, context_dict={}, request=None):
    template = get_template(template_src)
    html  = template.render(context_dict)
    
    # Create a file-like buffer to receive PDF data.
    buffer = io.BytesIO()
    
    # Resolve base_url for static files integration
    base_url = request.build_absolute_uri() if request else None

    # Generate PDF
    HTML(string=html, base_url=base_url).write_pdf(target=buffer)
    
    # Get the value of the BytesIO buffer and return response
    pdf = buffer.getvalue()
    buffer.close()
    return HttpResponse(pdf, content_type='application/pdf')
