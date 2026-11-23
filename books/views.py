from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.http import JsonResponse, FileResponse, Http404
from django.views.decorators.clickjacking import xframe_options_sameorigin
from django.db.models import Q, Count
from .models import Book
import os


def home(request):
    search = request.GET.get('search', '').strip()

    if search:
        books = Book.objects.filter(
            Q(book_name__icontains=search) |
            Q(author_name__icontains=search) |
            Q(category__icontains=search) |
            Q(description__icontains=search)
        )
        return render(request, 'home.html', {
            'books': books,
            'search': search,
            'is_search': True,
        })

    # Curated sections
    featured_books = Book.objects.filter(is_featured=True)
    if not featured_books.exists():
        featured_books = Book.objects.all()[:4]
    else:
        featured_books = featured_books[:4]

    trending_books = Book.objects.all()[:8]
    categories_with_count = Book.objects.values('category').annotate(
        count=Count('id')
    ).order_by('-count')[:6]

    total_books = Book.objects.count()
    total_categories = Book.objects.values('category').distinct().count()
    total_authors = Book.objects.values('author_name').distinct().count()
    total_digital = Book.objects.exclude(pdf='').exclude(pdf__isnull=True).count()

    return render(request, 'home.html', {
        'featured_books': featured_books,
        'books': trending_books,
        'categories': categories_with_count,
        'search': '',
        'is_search': False,
        'stats': {
            'total_books': total_books,
            'total_categories': total_categories,
            'total_authors': total_authors,
            'total_digital': total_digital,
        }
    })


def user_all(request):
    search = request.GET.get('search', '').strip()
    category = request.GET.get('category', '').strip()
    sort_by = request.GET.get('sort', 'newest').strip()

    books = Book.objects.all()

    if search:
        books = books.filter(
            Q(book_name__icontains=search) |
            Q(author_name__icontains=search) |
            Q(category__icontains=search) |
            Q(description__icontains=search)
        )

    if category and category != 'All':
        books = books.filter(category__iexact=category)

    # Sorting
    if sort_by == 'title_asc':
        books = books.order_by('book_name')
    elif sort_by == 'title_desc':
        books = books.order_by('-book_name')
    elif sort_by == 'author':
        books = books.order_by('author_name')
    elif sort_by == 'rating':
        books = books.order_by('-rating')
    elif sort_by == 'pdf':
        books = books.order_by('-pdf', '-id')
    else:
        books = books.order_by('-id')

    categories = Book.objects.values('category').annotate(
        count=Count('id')
    ).order_by('-count')

    return render(request, 'user_all.html', {
        'books': books,
        'search': search,
        'selected_category': category,
        'selected_sort': sort_by,
        'categories': categories,
        'total_results': books.count(),
    })


def get_pdf_page_count(pdf_field):
    if not pdf_field:
        return 0
    try:
        import re
        if os.path.exists(pdf_field.path):
            with open(pdf_field.path, 'rb') as f:
                return len(re.findall(rb'/Type\s*/Page\b', f.read()))
    except Exception:
        pass
    return 0


def book_detail(request, id):
    book = get_object_or_404(Book, id=id)

    # Related books from the same category
    related_books = Book.objects.filter(category=book.category).exclude(id=book.id)[:4]
    if related_books.count() < 3:
        fallback = Book.objects.exclude(id=book.id)[:4]
        related_books = (related_books | fallback).distinct()[:4]

    pdf_pages = get_pdf_page_count(book.pdf)
    pages = book.pages or (pdf_pages * 40 if pdf_pages else 208)
    read_time_hours = max(0.5, round((pages * 1.1) / 60, 1))

    return render(request, 'book_detail.html', {
        'book': book,
        'related_books': related_books,
        'read_time_hours': read_time_hours,
        'pdf_pages': pdf_pages,
    })


@xframe_options_sameorigin
def stream_pdf(request, id):
    book = get_object_or_404(Book, id=id)
    if not book.pdf:
        messages.error(request, f"Digital PDF for '{book.book_name}' is currently unavailable.")
        return redirect('book_detail', id=book.id)

    try:
        safe_name = "".join(c for c in book.book_name if c.isalnum() or c in (' ', '_', '-')).strip() or f"book_{book.id}"
        safe_filename = f"{safe_name.replace(' ', '_')}.pdf"
        response = FileResponse(book.pdf.open('rb'), content_type='application/pdf')
        response['Content-Disposition'] = f'inline; filename="{safe_filename}"'
        response['X-Frame-Options'] = 'SAMEORIGIN'
        response['Access-Control-Allow-Origin'] = '*'
        return response
    except Exception as e:
        messages.error(request, "Unable to read the requested PDF file.")
        return redirect('book_detail', id=book.id)


def download_pdf(request, id):
    book = get_object_or_404(Book, id=id)
    if not book.pdf:
        messages.error(request, f"Digital PDF for '{book.book_name}' is currently unavailable.")
        return redirect('book_detail', id=book.id)

    try:
        safe_name = "".join(c for c in book.book_name if c.isalnum() or c in (' ', '_', '-')).strip() or f"book_{book.id}"
        filename = f"{safe_name.replace(' ', '_')}.pdf"
        response = FileResponse(book.pdf.open('rb'), as_attachment=True, filename=filename)
        return response
    except Exception as e:
        messages.error(request, "Unable to read the requested PDF file.")
        return redirect('book_detail', id=book.id)


def quick_view_api(request, id):
    try:
        book = Book.objects.get(id=id)
        pdf_pages = get_pdf_page_count(book.pdf)
        data = {
            'status': 'success',
            'id': book.id,
            'book_name': book.book_name,
            'author_name': book.author_name,
            'category': book.category,
            'description': book.description,
            'rating': float(book.rating or 4.8),
            'pages': book.pages or (pdf_pages * 40 if pdf_pages else 208),
            'pdf_pages': pdf_pages,
            'language': book.language or 'English',
            'image_url': book.image.url if book.image else '',
            'has_pdf': bool(book.pdf),
            'pdf_url': book.pdf.url if book.pdf else '',
            'stream_url': f"/view-pdf/{book.id}/" if book.pdf else '',
            'detail_url': f"/book/{book.id}/",
            'download_url': f"/download-pdf/{book.id}/" if book.pdf else '',
        }
        return JsonResponse(data)
    except Book.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Book not found'}, status=404)


# ==========================================================
# ADMIN AUTHENTICATION & MANAGEMENT
# ==========================================================

def admin_login(request):
    if request.user.is_authenticated and request.user.is_staff:
        return redirect('admin_dashboard')

    if request.method == "POST":
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '').strip()

        if not username or not password:
            messages.error(request, "Please enter both username and password.")
            return redirect('admin_login')

        user = authenticate(username=username, password=password)

        if user is not None:
            login(request, user)
            messages.success(request, f"Welcome back, {user.first_name or user.username}!")
            next_url = request.GET.get('next') or 'admin_dashboard'
            return redirect(next_url)
        else:
            messages.error(request, "Invalid username or password credentials.")
            return redirect('admin_login')

    return render(request, 'admin_login.html')


@login_required(login_url='admin_login')
def admin_logout(request):
    logout(request)
    messages.success(request, "You have been logged out securely.")
    return redirect('home')


@login_required(login_url='admin_login')
def admin_dashboard(request):
    books = Book.objects.all()
    total_books = books.count()
    total_categories = books.values('category').distinct().count()
    total_digital = books.exclude(pdf='').exclude(pdf__isnull=True).count()
    total_authors = books.values('author_name').distinct().count()

    categories_breakdown = Book.objects.values('category').annotate(
        count=Count('id')
    ).order_by('-count')[:5]

    recent_books = books[:8]

    return render(request, 'admin_dashboard.html', {
        'books': recent_books,
        'total_books': total_books,
        'total_categories': total_categories,
        'total_digital': total_digital,
        'total_authors': total_authors,
        'categories_breakdown': categories_breakdown,
    })


@login_required(login_url='admin_login')
def all_books(request):
    search = request.GET.get('search', '').strip()
    category = request.GET.get('category', '').strip()

    books = Book.objects.all()

    if search:
        books = books.filter(
            Q(book_name__icontains=search) |
            Q(author_name__icontains=search) |
            Q(category__icontains=search)
        )

    if category and category != 'All':
        books = books.filter(category__iexact=category)

    categories = Book.objects.values_list('category', flat=True).distinct()

    return render(request, 'all_books.html', {
        'books': books,
        'search': search,
        'selected_category': category,
        'categories': categories,
        'total_books': Book.objects.count(),
        'filtered_count': books.count(),
    })


@login_required(login_url='admin_login')
def add_book(request):
    if request.method == "POST":
        book_name = request.POST.get('book_name', '').strip()
        category = request.POST.get('category', '').strip()
        author_name = request.POST.get('author_name', '').strip()
        description = request.POST.get('description', '').strip()
        rating = request.POST.get('rating', '4.8').strip()
        pages = request.POST.get('pages', '280').strip()
        language = request.POST.get('language', 'English').strip()
        is_featured = request.POST.get('is_featured') == 'on'

        image = request.FILES.get('image')
        pdf = request.FILES.get('pdf')

        if not book_name or not author_name or not category or not description:
            messages.error(request, "Please fill in all required fields.")
            return render(request, 'add_book.html')

        try:
            rating_val = float(rating) if rating else 4.8
            pages_val = int(pages) if pages else 280
        except ValueError:
            rating_val = 4.8
            pages_val = 280

        book = Book.objects.create(
            book_name=book_name,
            category=category,
            author_name=author_name,
            description=description,
            rating=rating_val,
            pages=pages_val,
            language=language or 'English',
            is_featured=is_featured,
            image=image,
            pdf=pdf
        )

        messages.success(request, f"Book '{book.book_name}' was added to the library!")
        return redirect('all_books')

    # Provide existing categories for quick auto-suggest
    existing_categories = Book.objects.values_list('category', flat=True).distinct()
    return render(request, 'add_book.html', {
        'existing_categories': existing_categories
    })


@login_required(login_url='admin_login')
def update_book(request, id):
    book = get_object_or_404(Book, id=id)

    if request.method == "POST":
        book.book_name = request.POST.get('book_name', '').strip()
        book.category = request.POST.get('category', '').strip()
        book.author_name = request.POST.get('author_name', '').strip()
        book.description = request.POST.get('description', '').strip()
        
        rating = request.POST.get('rating', '').strip()
        pages = request.POST.get('pages', '').strip()
        language = request.POST.get('language', 'English').strip()
        book.is_featured = request.POST.get('is_featured') == 'on'

        if rating:
            try:
                book.rating = float(rating)
            except ValueError:
                pass

        if pages:
            try:
                book.pages = int(pages)
            except ValueError:
                pass

        book.language = language or 'English'

        # Handle image upload
        if request.FILES.get('image'):
            book.image = request.FILES.get('image')

        # Handle PDF upload or removal
        if request.FILES.get('pdf'):
            book.pdf = request.FILES.get('pdf')
        elif request.POST.get('remove_pdf') == '1':
            book.pdf = None

        book.save()
        messages.success(request, f"'{book.book_name}' has been successfully updated!")
        return redirect('all_books')

    existing_categories = Book.objects.values_list('category', flat=True).distinct()
    return render(request, 'update_book.html', {
        'book': book,
        'existing_categories': existing_categories
    })


@login_required(login_url='admin_login')
def delete_book(request, id):
    book = get_object_or_404(Book, id=id)
    title = book.book_name
    book.delete()
    messages.success(request, f"Book '{title}' was permanently deleted.")
    return redirect('all_books')
