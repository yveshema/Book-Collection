import datetime

from django.shortcuts import render, get_object_or_404
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.views import generic

from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.contrib.auth.decorators import permission_required
from catalog.models import Book, Author, BookInstance, Genre, Language

# from catalog.forms import RenewBookModelForm
from catalog.forms import RenewBookForm

def index(request):
    """View function for home page of site."""

    # Generate counts of some of the main objects
    num_books = Book.objects.all().count()
    num_instances = BookInstance.objects.all().count()

    # Available books (status = 'a'))
    num_instances_available = BookInstance.objects.filter(status__exact='a').count()

    # The 'all()' is implied by default.
    num_authors = Author.objects.count()

    # Number of visits to this view, as counted in the session variable.
    num_visits = request.session.get('num_visits', 0)
    request.session['num_visits'] = num_visits + 1

    context = {
        'num_books': num_books,
        'num_instances': num_instances,
        'num_instances_available': num_instances_available,
        'num_authors': num_authors,
        'num_visits': num_visits,
    }

    # Render the HTML template index.html with the data in the context variable
    return render(request, 'index.html', context=context)


class BookListView(generic.ListView):
    model = Book
    paginate_by = 10


class BookDetailView(generic.DetailView):
    model = Book

class AuthorListView(generic.ListView):
    model = Author
    paginate_by = 10

class AuthorDetailView(generic.DetailView):
    model = Author

class LoanedBooksByUserListView(LoginRequiredMixin, generic.ListView):
    """Generic class-based view listing books on loan to current user."""
    model = BookInstance
    template_name = 'catalog/bookinstance_list_borrowed_user.html'
    paginate_by = 10

    def get_queryset(self):
        return BookInstance.objects\
                .filter(borrower=self.request.user)\
                .filter(status__exact='o')\
                .order_by('due_back')

class AllBorrowedBooksListView(PermissionRequiredMixin, generic.ListView):
    """Generic class-based view listing all borrowed books."""
    permission_required = ('catalog.can_mark_returned',)
    model = BookInstance
    template_name='catalog/bookinstance_list_all_borrowed.html'
    paginate_by = 10

    def get_queryset(self):
        return BookInstance.objects\
                .filter(borrower__isnull=False)\
                .filter(status__exact='o')\
                .order_by('due_back')


@permission_required('catalog.can_mark_returned')
def renew_book_librarian(request, pk):
    book_instance = get_object_or_404(BookInstance, pk=pk)

    # If this is a POST request then process the Form data
    if request.method == 'POST':

        # Create a form instance and populate it with data
        # from the request (binding)
        # form = RenewBookModelForm(request.POST)
        form = RenewBookForm(request.POST)

        # Check if the form is valid
        if form.is_valid():
            # Process the data in form.cleaned_data as required
            # (here we just write it to the model due_back field
            # book_instance.due_back = form.cleaned_data['due_back']
            book_instance.due_back = form.cleaned_data['renewal_date']
            book_instance.save()

            # redirect to a new URL
            return HttpResponseRedirect(reverse('all-borrowed'))

    # If this is a GET (or any other method) create the default form.
    else:
        proposed_renewal_date = datetime.date.today() + datetime.timedelta(weeks=3)
        # form = RenewBookModelForm(initial={'due_back': proposed_renewal_date})
        form = RenewBookForm(initial={'renewal_date': proposed_renewal_date})

    context = {
        'form': form,
        'book_instance': book_instance,
    }

    return render(request, 'catalog/book_renew_librarian.html', context)


from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy

from catalog.models import Author

class AuthorCreate(PermissionRequiredMixin, CreateView):
    permission_required = ('catalog.can_mark_returned',)
    model = Author
    fields = '__all__'
    initial = {'date_of_death':'05/01/2018'}

class AuthorUpdate(PermissionRequiredMixin, UpdateView):
    permission_required = ('catalog.can_mark_returned',)
    model = Author
    fields = ['first_name','last_name','date_of_birth','date_of_death']

class AuthorDelete(PermissionRequiredMixin, DeleteView):
    permission_required = ('catalog.can_mark_returned',)
    model = Author
    success_url = reverse_lazy('authors')

from django.forms.models import inlineformset_factory

LanguageFormset = inlineformset_factory(
    Language, Book, fields=('language',)
)

class BookCreate(PermissionRequiredMixin, CreateView):
    permission_required = ('catalog.can_mark_returned',)
    model = Book
    fields = '__all__'

class BookUpdate(PermissionRequiredMixin, UpdateView):
    permission_required = ('catalog.can_mark_returned',)
    model = Book
    fields = ['title','author','summary','isbn','language','genre']

class BookDelete(PermissionRequiredMixin, DeleteView):
    permission_required = ('catalog.can_mark_returned',)
    model = Book
    success_url = reverse_lazy('books')
