from django import forms
from django.utils.text import slugify
from .models import Article, Category, Comment, ReviewNote


class ArticleForm(forms.ModelForm):
    class Meta:
        model  = Article
        fields = ['title', 'category', 'tags', 'cover_image', 'excerpt', 'body']
        widgets = {
            'tags': forms.CheckboxSelectMultiple(),
            'body': forms.Textarea(attrs={'rows': 15}),
            'excerpt': forms.Textarea(attrs={'rows': 3}),
        }
        labels = {
            'excerpt': 'Short Summary (optional)',
        }
        help_texts = {
            'excerpt': 'A 1–2 sentence preview shown on the article list page and search results. '
                       'Leave blank and it will be auto-generated from the first 30 words of your article.',
        }


class ReviewForm(forms.Form):
    ACTION_CHOICES = [
        ('approved', 'Approve & Publish'),
        ('rejected', 'Reject & Request Changes'),
    ]
    action = forms.ChoiceField(choices=ACTION_CHOICES, widget=forms.RadioSelect)
    note   = forms.CharField(
                 widget=forms.Textarea(attrs={'rows': 4}),
                 required=False,
                 help_text='Required when rejecting. Will be shown to the author.',
             )

    def clean(self):
        cleaned_data = super().clean()
        action = cleaned_data.get('action')
        note   = cleaned_data.get('note', '').strip()
        if action == 'rejected' and not note:
            raise forms.ValidationError('Please provide feedback when rejecting an article.')
        return cleaned_data


class CategoryForm(forms.ModelForm):
    class Meta:
        model  = Category
        fields = ['name', 'description']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }

    def save(self, commit=True):
        category = super().save(commit=False)
        if not category.slug:
            base = slugify(category.name)
            slug = base
            counter = 1
            while Category.objects.filter(slug=slug).exclude(pk=category.pk).exists():
                slug = f'{base}-{counter}'
                counter += 1
            category.slug = slug
        if commit:
            category.save()
        return category


class CommentForm(forms.ModelForm):
    class Meta:
        model  = Comment
        fields = ['body']
        widgets = {
            'body': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Write a comment...'}),
        }
        labels = {'body': ''}
