from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from .models import *
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from datetime import date, datetime
from django.utils import timezone
from collections import Counter
import json
from itertools import zip_longest
from django.db.models import Max

# Create your views here.
def index(request):
    return render(request, "home_page.html")

def sign_in(request):
    if request.method == 'POST':
        try:
            username = request.POST['username']
            password = request.POST['password']

            user = authenticate(request, username=username, password=password)
            
            if user is None:
                messages.success(request, 'Invalid login credentials.')
                return redirect('signin')
            
            userDetails = UserDetail.objects.get(user=user)

            if user is not None and userDetails.is_active:
                login(request, user)
                return redirect('home')
            elif user is not None and not userDetails.is_active:
                messages.error(request, 'User account is not yet approved by the admin.')
            else:
                messages.error(request, 'Invalid login credentials.')

        except Exception as e:
            messages.error(request, f'Error during login: {str(e)}')
    return render(request, "signin_page.html")

def sign_up(request):
    if request.method == 'POST':
        try:
            fullname = request.POST['fullname']
            email = request.POST['email']
            username = request.POST['username']
            password = request.POST['password']
            confirm_password = request.POST['confirm_password']
            
            if User.objects.filter(username=username).exists():
                messages.error(request, 'Username already exists.')
                return redirect('signup')

            if password != confirm_password:
                messages.error(request, 'Passwords do not match.')
                return redirect('signup')
            
            user = User.objects.create_user(first_name=fullname, username=username, password=password, email=email)
            UserDetail.objects.create(user=user)

            messages.success(request, 'Registration successful. Now wait till admin approve your account. After that you can login.')
            return redirect('signin')
            
        except Exception as e:
            messages.error(request, f'Error during registration: {str(e)}')
    return render(request, "register_page.html")

def user_logout(request):
    try:
        logout(request)
        return redirect('home')

    except Exception as e:
        messages.error(request, f'Error during logout: {str(e)}')
        return redirect('home')
    
def change_password(request):
    if request.method == 'POST':
        try:
            username = request.POST['username']
            old_password = request.POST['old_password']
            new_password = request.POST['new_password']

            # Validate if the fields are not empty
            if not username or not old_password or not new_password:
                messages.error(request, 'All fields are required.')
                return redirect('change_password')

            user = authenticate(request, username=username, password=old_password)

            if user is not None:
                # Check if the new password is the same as the old password
                if old_password == new_password:
                    messages.error(request, 'New password must be different from the old password.')
                    return redirect('change_password')

                # Change the user's password
                user.set_password(new_password)
                user.save()

                messages.success(request, 'Password changed successfully. Please login with your new password.')
                return redirect('signin')
            else:
                messages.error(request, 'Invalid username or password. Please try again.')

        except Exception as e:
            messages.error(request, f'Error during change password: {str(e)}')

    return render(request, "changePassword_page.html")

@login_required
def management(request):
    procedures = Procedure.objects.all()
    folders = Folder.objects.filter(user=request.user).order_by('order')
    shifts = Shift.objects.filter(user=request.user).order_by('order')
    return render(request, "management_page.html", {'procedures': procedures, 'folders': folders, 'shifts': shifts})

@login_required
def add_procedure(request):
    if request.method == 'POST':
        cpt = request.POST.get('cpt')
        modality = request.POST.get('modality')
        description = request.POST.get('description')
        rvu = request.POST.get('rvu')
        
        # Check if a procedure with the same data already exists
        existing_procedure = Procedure.objects.filter(cpt=cpt, modality=modality, description=description, rvu=rvu)

        if existing_procedure:
            messages.success(request, f'Procedure already exists in the database')
            return JsonResponse({'success': True})

        try:
            # Create Procedure instance
            Procedure.objects.create(cpt=cpt, modality=modality, description=description, rvu=rvu)
            return JsonResponse({'success': True})
        except Exception as e:
            messages.success(request, f'Error during add procedure: {str(e)}')
            return JsonResponse({'success': True})
    
    messages.success(request, f'Invalid request method')
    return JsonResponse({'success': True})

@login_required
def get_procedure(request, procedure_id):
    procedure = get_object_or_404(Procedure, id=procedure_id)
    return JsonResponse({'success': True, 'procedure': {
        'id': procedure.id,
        'cpt': procedure.cpt,
        'modality': procedure.modality,
        'description': procedure.description,
        'rvu': procedure.rvu,
    }})

@login_required
def edit_procedure(request):
    if request.method == 'POST':
        procedure_id = request.POST.get('procedure_id')
        cpt = request.POST.get('cpt')
        modality = request.POST.get('modality')
        description = request.POST.get('description')
        rvu = request.POST.get('rvu')

        try:
            procedure = Procedure.objects.get(id=procedure_id)
            procedure.cpt = cpt
            procedure.modality = modality
            procedure.description = description
            procedure.rvu = rvu
            procedure.save()
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    return JsonResponse({'success': False, 'error': 'Invalid request method'})

@login_required
def delete_procedure(request, procedure_id):
    try:
        procedure = Procedure.objects.get(id=procedure_id)
        procedure.delete()
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})
 
@login_required    
def add_folder(request):
    if request.method == 'POST':
        folder_name = request.POST.get('folder_name')
        if folder_name:
            # Get the latest order for the user's folders
            latest_order = Folder.objects.filter(user=request.user).aggregate(Max('order'))['order__max']

            # If there are no folders yet, set order to 1, otherwise, increment the latest order
            order = 1 if latest_order is None else latest_order + 1

            # Create the Folder instance with the calculated order
            Folder.objects.create(name=folder_name, user=request.user, order=order)
    return redirect('management')

@login_required
def delete_folder(request):
    if request.method == 'POST':
        folder_id = request.POST.get('folder_id')
        try:
            folder = Folder.objects.get(id=folder_id)
            folder.delete()
            return redirect('management')
        except Exception as e:
            messages.success(request, f'Error during delete: {str(e)}')
            return redirect('management')

    return redirect('management')

@login_required
def update_folder_order(request):
    if request.method == 'POST':
        folder_order = request.POST.get('folder_order')
        folder_order = json.loads(folder_order)

        # Update the order in the database
        for data in folder_order:
            folder_id = data['id']
            new_order = data['order']
            print(f"folder_id: {folder_id}\tnew_order: {new_order}")
            folder = Folder.objects.get(id=folder_id)
            folder.order = new_order
            folder.save()

        return JsonResponse({'success': True})

    return JsonResponse({'success': False})

@login_required
def move_selected_to_folder(request):
    if request.method == 'POST':
        procedure_ids_string = request.POST.get('procedure_ids')
        procedure_ids = procedure_ids_string.split(',')
        folder_id = request.POST.get('folder_id')

        try:
            folder = Folder.objects.get(id=folder_id)
            existing_procedures = folder.folderprocedure_set.all()
            existing_procedure_ids = [entry.procedure.id for entry in existing_procedures]

            # Create FolderProcedure entries for each selected procedure
            new_records = 0
            existing_records = 0
            for procedure_id in procedure_ids:
                procedure_id_int = int(procedure_id)
                if procedure_id_int not in existing_procedure_ids:
                    procedure = Procedure.objects.get(id=procedure_id_int)
                    FolderProcedure.objects.create(folder=folder, procedure=procedure)
                    new_records += 1
                else:
                    existing_records += 1

            if existing_records > 0 and new_records == 0:
                messages.success(request, f'{existing_records} record(s) already exist in {folder.name} and were not moved.')
                return redirect('management')
            
            if existing_records == 0 and new_records > 0:
                messages.success(request, f'Total of {new_records} record(s) moved to {folder.name}')
                return redirect('management')
            if existing_records > 0 and new_records > 0:
                messages.success(request, f'Total of {new_records} record(s) moved to {folder.name}, because {existing_records} record(s) already exist in the folder.')
                return redirect('management')
            return redirect('management')
        except Exception as e:
            messages.success(request, f'Error during moving data: {str(e)}')
            return redirect('management')

    return redirect('management')

@login_required
def get_folder_details(request, folder_id):
    folder = Folder.objects.get(id=folder_id)
    records = FolderProcedure.objects.filter(folder=folder).order_by('order').values('id', 'procedure__description')

    data = {
        'folderName': folder.name,
        'records': list(records),
    }

    return JsonResponse(data)

@login_required
def delete_record(request):
    if request.method == 'POST':
        record_id = request.POST.get('record_id')
        try:
            record = FolderProcedure.objects.get(id=record_id)
            record.delete()
            return redirect('management')
        except Exception as e:
            messages.success(request, f'Error during delete: {str(e)}')
            return redirect('management')

    return redirect('management')

@login_required
def update_folder_procedure_order(request):
    if request.method == 'POST':
        folder_procedure_order = json.loads(request.POST.get('folder_procedure_order'))

        try:
            for data in folder_procedure_order:
                folder_procedure_id = data['id']
                new_order = data['order']

                folder_procedure = FolderProcedure.objects.get(id=folder_procedure_id)
                folder_procedure.order = new_order
                folder_procedure.save()

            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    return JsonResponse({'error': 'Invalid request'}, status=400)

@login_required    
def add_shift(request):
    if request.method == 'POST':
        shift_name = request.POST.get('shift_name')
        if shift_name:
            # Get the latest order for the user's folders
            latest_order = Shift.objects.filter(user=request.user).aggregate(Max('order'))['order__max']

            # If there are no folders yet, set order to 1, otherwise, increment the latest order
            order = 1 if latest_order is None else latest_order + 1

            # Create the Folder instance with the calculated order
            Shift.objects.create(name=shift_name, user=request.user, order=order)
    return redirect('management')

@login_required
def delete_shift(request):
    if request.method == 'POST':
        shift_id = request.POST.get('shift_id')
        try:
            shift = Shift.objects.get(id=shift_id)
            shift.delete()
            return redirect('management')
        except Exception as e:
            messages.success(request, f'Error during delete: {str(e)}')
            return redirect('management')

    return redirect('management')

@login_required
def update_shift_order(request):
    if request.method == 'POST':
        shift_order = request.POST.get('shift_order')
        shift_order = json.loads(shift_order)

        # Update the order in the database
        for data in shift_order:
            shift_id = data['id']
            new_order = data['order']
            print(f"shift_id: {shift_id}\tnew_order: {new_order}")
            shift = Shift.objects.get(id=shift_id)
            shift.order = new_order
            shift.save()

        return JsonResponse({'success': True})

    return JsonResponse({'success': False})


@login_required
def main(request):
    folders = Folder.objects.filter(user=request.user).order_by('order')
    shifts = Shift.objects.filter(user=request.user)
    return render(request, "main_page.html", {"folders": folders, "shifts": shifts})

@login_required
def get_total_rvus(request):
    if request.method == 'GET':
        selected_date = request.GET.get('selected_date')

        try:
            if selected_date:
                # Get Procedure records for the selected date
                records = Record.objects.filter(created_at__date=selected_date, user=request.user)

                # Calculate total RVUs
                total_rvus = records.aggregate(total_rvu=models.Sum('procedure__rvu'))['total_rvu'] or 0

                # Return the total RVUs as JSON response
                return JsonResponse({'total_rvus': round(total_rvus, 3)})
            return JsonResponse({'error': 'Date Not picked'}, status=400)

        except ValueError:
            # Handle invalid date format
            return JsonResponse({'error': 'Invalid date format'}, status=400)

    return JsonResponse({'error': 'Invalid request method'}, status=400)

@login_required
def get_folder_records(request, folder_id):
    folder = Folder.objects.get(id=folder_id)
    records = FolderProcedure.objects.filter(folder=folder).order_by('order').values('id', 'procedure__description')

    # Convert the records to a list
    records_list = list(records)

    # If the number of records is odd, add an empty record with None values
    if len(records_list) % 2 == 1:
        records_list.append({'id': None, 'procedure__description': None})

    # Create pairs of records using zip_longest
    pairs_of_records = list(zip_longest(*[iter(records_list)] * 2, fillvalue=None))

    # Extract relevant information for each pair
    data = [{'record1': {'id': record1['id'], 'description': record1['procedure__description']},
             'record2': {'id': record2['id'], 'description': record2['procedure__description']}}
            for record1, record2 in pairs_of_records]

    return JsonResponse({'data': data})

@login_required
def get_procedure_records(request):
    if request.method == 'GET':
        record_id = request.GET.get('record_id')
        selected_shift = request.GET.get('selected_shift')
        selected_date = request.GET.get('selected_date')

        try:
            # Get the procedure based on the record ID
            procedure_record = get_object_or_404(FolderProcedure, id=record_id)

            # Get additional information based on the selected shift
            if selected_shift:
                shift = Shift.objects.get(id=selected_shift)

                Record.objects.create(
                    user=request.user,
                    shift=shift,
                    procedure=procedure_record.procedure,
                    created_at=datetime.combine(datetime.strptime(selected_date, '%Y-%m-%d').date(), timezone.now().time()),
                )
                
                shift_name = shift.name
            else:
                Record.objects.create(
                    user=request.user,
                    procedure=procedure_record.procedure,
                    created_at=datetime.combine(datetime.strptime(selected_date, '%Y-%m-%d').date(), timezone.now().time()),
                )
                shift_name = None

            # Return procedure details and shift name as JSON response
            return JsonResponse({
                'created_at': selected_date,
                'description': procedure_record.procedure.description,
                'shift_name': shift_name,
            })

        except Procedure.DoesNotExist:
            return JsonResponse({'error': 'Procedure not found'}, status=404)

    return JsonResponse({'error': 'Invalid request method'}, status=400)

@login_required
def reports(request):
    # Get user shifts
    user_shifts = Shift.objects.filter(user=request.user)

    # Get distinct values for Modality, Description, and CPT
    distinct_descriptions = Record.objects.values_list('procedure__description', flat=True).distinct()
    distinct_cpts = Record.objects.values_list('procedure__cpt', flat=True).distinct()

    # Get today's date
    today_date = date.today()
    
    # Pass data to the template
    context = {
        'user_shifts': user_shifts,
        'distinct_descriptions': distinct_descriptions,
        'distinct_cpts': distinct_cpts,
        'today_date': today_date,
    }

    return render(request, "reports_page.html", context)

def get_filtered_data_from_database(start_date, end_date, shift_id, modality, description, cpt, ur):
    # Define the base queryset
    queryset = Record.objects.filter(user=ur)

    # Apply filters based on user input
    if start_date:
        start_date = datetime.strptime(start_date, '%Y-%m-%d')
        queryset = queryset.filter(created_at__date__gte=start_date)

    if end_date:
        end_date = datetime.strptime(end_date, '%Y-%m-%d')
        queryset = queryset.filter(created_at__date__lte=end_date)
        
    if modality:
        queryset = queryset.filter(procedure__modality=modality)

    if description:
        queryset = queryset.filter(procedure__description__icontains=description)
        # Use OR condition for partial matches in Description
        # query_description = Q()
        # for i in range(1, len(description) + 1):
        #     query_description |= Q(procedure__description__icontains=description[:i])
        # queryset = queryset.filter(query_description)

    if cpt:
        queryset = queryset.filter(procedure__cpt__icontains=cpt)
        # Use OR condition for partial matches in CPT
        # query_cpt = Q()
        # for i in range(1, len(cpt) + 1):
        #     query_cpt |= Q(procedure__cpt__icontains=cpt[:i])
        # queryset = queryset.filter(query_cpt)
    
    # If shift_id is provided, filter using ShiftProcedure
    if shift_id:
        shift = Shift.objects.get(id=shift_id)
        queryset = queryset.filter(shift=shift)

    # Return the filtered data
    return queryset

@login_required
def get_filtered_data(request):
    ur = request.user
    if request.method == 'GET':
        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')
        shift_id = request.GET.get('shift_id')
        modality = request.GET.get('modality')
        description = request.GET.get('description')
        cpt = request.GET.get('cpt')
        try:
            # Get filtered data from the database
            filtered_data = get_filtered_data_from_database(start_date, end_date, shift_id, modality, description, cpt, ur)

            # Calculate modality distribution
            modality_distribution = Counter(item.procedure.modality for item in filtered_data)
            
            data = [
                {
                    'record_id': item.id,
                    'date_time': item.created_at.strftime("%m/%d/%y %H%M"),
                    'cpt': item.procedure.cpt,
                    'shift': item.shift.name if item.shift else None,
                    'modality': item.procedure.modality,
                    'description': item.procedure.description,
                    'rvu': item.procedure.rvu
                }
                for item in filtered_data
            ]

            return JsonResponse({'data': data, 'modality_distribution': dict(modality_distribution)})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    return redirect('reports')

@login_required
def delete_record(request):
    record_id = request.POST.get('record_id')

    try:
        # Find the record using the provided parameters
        record = Record.objects.get(id=record_id)

        record.delete()
        return JsonResponse({'success': True})
    except Record.DoesNotExist:
        return JsonResponse({'error': 'Record not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)