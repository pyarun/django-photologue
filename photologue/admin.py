from django.contrib import admin
from django import forms
from django.conf import settings
from django.contrib.admin import widgets 
from django.template.loader import render_to_string
from django.utils.safestring import mark_safe
from .models import Gallery, Photo, GalleryUpload, PhotoEffect, PhotoSize, \
    Watermark, GalleryInfo

USE_CKEDITOR = getattr(settings, 'PHOTOLOGUE_USE_CKEDITOR', False)

if USE_CKEDITOR:
    from ckeditor.widgets import CKEditorWidget

class GalleryInfoInline(admin.TabularInline):
    model = GalleryInfo

class GalleryAdminForm(forms.ModelForm):
    if USE_CKEDITOR:
        description = forms.CharField(widget=CKEditorWidget())

    class Meta:
        model = Gallery

ADMIN_MEDIA_PREFIX = "/static/admin/"

class FilteredSelectMultipleCustom( widgets.FilteredSelectMultiple ):
    class Media:
        js = ( ADMIN_MEDIA_PREFIX + "js/core.js",
              ADMIN_MEDIA_PREFIX + "js/SelectBox.js",
              ADMIN_MEDIA_PREFIX + "js/SelectFilter2.js" )

    def __init__( self, verbose_name, leftHandSideQuerySet,
rightHandSideQuerySet, attrs={} ):
        self.verbose_name = verbose_name
        self.leftHandQuerySet = leftHandSideQuerySet
        self.rightHandSideQuerySet = rightHandSideQuerySet
        self.attrs = attrs
        super( FilteredSelectMultipleCustom, self ).__init__( verbose_name,
False, attrs )

    """
    Takes two queryset as init argument and use those
    """
    def render( self, name, values, *args, **kwargs ):
        dictionary = {
            'name':name,
            'left':self.leftHandQuerySet,
            'right':self.rightHandSideQuerySet,
            'verbose_name':self.verbose_name
        }
        s = render_to_string( "photologue/multiple_select.html", dictionary )
        return mark_safe( u''.join( s ) )


class GalleryAdmin(admin.ModelAdmin):
    #inlines = (GalleryInfoInline, )
    list_display = ('title', 'date_added', 'photo_count', 'is_public')
    list_filter = ['date_added', 'is_public']
    date_hierarchy = 'date_added'
    prepopulated_fields = {'title_slug': ('title',)}
    #filter_horizontal = ('photos',)
    form = GalleryAdminForm
    raw_id_fields = ("photos", )
    def __init__(self, *args, **kwargs):
        self.object_id = None
        super( GalleryAdmin, self ).__init__( *args, **kwargs )

    def get_object( self, request, object_id ):
        self.object_id = object_id
        return super( GalleryAdmin, self ).get_object( request, object_id)

        
    #form.save_m2m = save_my_m2m
    def save_model( self , request, obj, form, change ):
        super(GalleryAdmin, self).save_model( request, obj, form, change )
        self.save_m2m = form.save_m2m
        self.request = request
        self.form_data = form
        self.obj = obj
        
        def save_my_m2m():
            GalleryInfo.objects.filter(gallery=self.obj.id).delete();
            photosRel = self.request.REQUEST.getlist( 'photos' );
            photosEle = self.form_data.cleaned_data['photos']
      
            i = 1;
            for e in photosRel:
                GalleryInfo( gallery=self.obj, photo=photosEle.get( id=e ) , number=i ).save()
                i = i + 1
            
            del self.form_data.cleaned_data['photos']
            self.save_m2m()
        
        form.save_m2m = save_my_m2m
        
    def formfield_for_manytomany( self, db_field, request=None, **kwargs ):
        if db_field.column == 'photos':
            selectedQuerySet = GalleryInfo.objects.filter(gallery=self.object_id).order_by( 'number' )
            selected = []
            for s in selectedQuerySet:
                selected.append(s.photo)
            notSelected = Photo.objects.exclude(id__in=selectedQuerySet.values("photo"))
            kwargs['widget'] = FilteredSelectMultipleCustom(db_field.verbose_name, notSelected, selected)
            kwargs['help_text'] = ''
            return db_field.formfield( **kwargs )


class PhotoAdminForm(forms.ModelForm):
    if USE_CKEDITOR:
        caption = forms.CharField(widget=CKEditorWidget())

    class Meta:
        model = Photo


class PhotoAdmin(admin.ModelAdmin):
    list_display = ('title', 'date_taken', 'date_added', 'is_public', 'tags', 'view_count', 'admin_thumbnail')
    list_filter = ['date_added', 'is_public']
    search_fields = ['title', 'title_slug', 'caption']
    list_per_page = 10
    prepopulated_fields = {'title_slug': ('title',)}
    form = PhotoAdminForm


class PhotoEffectAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'color', 'brightness', 'contrast', 'sharpness', 'filters', 'admin_sample')
    fieldsets = (
        (None, {
            'fields': ('name', 'description')
        }),
        ('Adjustments', {
            'fields': ('color', 'brightness', 'contrast', 'sharpness')
        }),
        ('Filters', {
            'fields': ('filters',)
        }),
        ('Reflection', {
            'fields': ('reflection_size', 'reflection_strength', 'background_color')
        }),
        ('Transpose', {
            'fields': ('transpose_method',)
        }),
    )


class PhotoSizeAdmin(admin.ModelAdmin):
    list_display = ('name', 'width', 'height', 'crop', 'pre_cache', 'effect', 'increment_count')
    fieldsets = (
        (None, {
            'fields': ('name', 'width', 'height', 'quality')
        }),
        ('Options', {
            'fields': ('upscale', 'crop', 'pre_cache', 'increment_count')
        }),
        ('Enhancements', {
            'fields': ('effect', 'watermark',)
        }),
    )


class WatermarkAdmin(admin.ModelAdmin):
    list_display = ('name', 'opacity', 'style')


class GalleryUploadAdmin(admin.ModelAdmin):

    def has_change_permission(self, request, obj=None):
        return False  # To remove the 'Save and continue editing' button


admin.site.register(Gallery, GalleryAdmin)
admin.site.register(GalleryUpload, GalleryUploadAdmin)
admin.site.register(Photo, PhotoAdmin)
admin.site.register(PhotoEffect, PhotoEffectAdmin)
admin.site.register(PhotoSize, PhotoSizeAdmin)
admin.site.register(Watermark, WatermarkAdmin)
