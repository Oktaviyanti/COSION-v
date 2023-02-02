import os, shutil
from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.shortcuts import render
from django.views.generic import TemplateView

from .forms import FormUpload
from .acac_segmentation import Segmentation
# from .morbac import Segmentation

path = os.path.join(settings.BASE_DIR, settings.MEDIA_ROOT)
base_path = path + '/codion'

def index(request):
    template = 'pages/home.html'
    return render(request, template)

def delete_file(request):
    from django.http import JsonResponse
    try:
        shutil.rmtree(base_path)
        return JsonResponse(
            {
                "success": "Semua file pada %s sudah dihapus!" % base_path
            },
            safe=False
        )
    except Exception as e:
        resp = {
            "err_msg": "Tidak dapat menghapus %s. Karena %s" % (base_path, e)
        }
        return JsonResponse(resp, safe=False)

class About(TemplateView):
    template_name = 'pages/about.html'

class SegmentationView(TemplateView):
    template_name = 'codion/segmentation.html'

    def __get_segmentation(self, base, name, url):
        segment = Segmentation(base, name)
        segment = segment.get_image()
        result = {
            "file_url": url,
            "file_out": segment[0],
            "info": segment[1]
        }
        return result

    def post(self, request, *args, **kwargs):
        form = FormUpload(request.POST or None, request.FILES or None)
        context = self.get_context_data(form=form)
        if form.is_valid():
            file_img = form.cleaned_data.get('images')
            fss = FileSystemStorage(location=base_path)
            f_save = fss.save(file_img.name, file_img)
            file_url = '/media/codion/' + f_save
            result = self.__get_segmentation(fss.base_location, f_save, file_url)
            context.update(result)
            # return self.render_to_response(context)
        return self.render_to_response(context)
    
    def get(self, request, *args, **kwargs):
        return self.post(request, *args, **kwargs)
