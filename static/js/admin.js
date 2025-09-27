// Admin Panel JavaScript

$(document).ready(function() {
    // Initialize tooltips
    $('[data-bs-toggle="tooltip"]').tooltip();
    
    // Initialize popovers
    $('[data-bs-toggle="popover"]').popover();
    
    // Sidebar toggle for mobile
    $('.sidebar-toggle').click(function() {
        $('.sidebar').toggleClass('show');
    });
    
    // Close sidebar when clicking outside on mobile
    $(document).click(function(e) {
        if ($(window).width() <= 768) {
            if (!$(e.target).closest('.sidebar, .sidebar-toggle').length) {
                $('.sidebar').removeClass('show');
            }
        }
    });
    
    // Auto-save form data
    $('form input, form textarea, form select').on('input change', function() {
        var form = $(this).closest('form');
        var formId = form.attr('id') || 'admin-form';
        var formData = form.serialize();
        localStorage.setItem('admin-form-' + formId, formData);
    });
    
    // Restore form data on page load
    $('form').each(function() {
        var form = $(this);
        var formId = form.attr('id') || 'admin-form';
        var savedData = localStorage.getItem('admin-form-' + formId);
        
        if (savedData) {
            // Parse and restore form data
            var params = new URLSearchParams(savedData);
            params.forEach(function(value, key) {
                var field = form.find('[name="' + key + '"]');
                if (field.length) {
                    if (field.is(':checkbox, :radio')) {
                        field.prop('checked', value === 'on' || field.val() === value);
                    } else {
                        field.val(value);
                    }
                }
            });
        }
    });
    
    // Clear saved form data on successful submit
    $('form').submit(function() {
        var form = $(this);
        var formId = form.attr('id') || 'admin-form';
        localStorage.removeItem('admin-form-' + formId);
    });
    
    // Image upload preview
    $('input[type="file"]').change(function() {
        var input = this;
        var preview = $(input).siblings('.image-preview');
        
        if (input.files && input.files[0]) {
            var reader = new FileReader();
            
            reader.onload = function(e) {
                if (preview.length) {
                    preview.html('<img src="' + e.target.result + '" class="img-fluid" style="max-height: 200px;">');
                } else {
                    // Create preview container if it doesn't exist
                    $(input).after('<div class="image-preview mt-2"><img src="' + e.target.result + '" class="img-fluid" style="max-height: 200px;"></div>');
                }
            };
            
            reader.readAsDataURL(input.files[0]);
        }
    });
    
    // Bulk actions
    $('.bulk-action').change(function() {
        var action = $(this).val();
        var checkedItems = $('.item-checkbox:checked');
        
        if (action && checkedItems.length > 0) {
            if (confirm('Are you sure you want to ' + action + ' ' + checkedItems.length + ' item(s)?')) {
                var itemIds = [];
                checkedItems.each(function() {
                    itemIds.push($(this).val());
                });
                
                performBulkAction(action, itemIds);
            }
        }
        
        $(this).val('');
    });
    
    // Select all checkbox
    $('.select-all').change(function() {
        var isChecked = $(this).is(':checked');
        $('.item-checkbox').prop('checked', isChecked);
        updateBulkActions();
    });
    
    // Individual checkbox change
    $('.item-checkbox').change(function() {
        updateBulkActions();
    });
    
    // Delete confirmation
    $('.delete-btn').click(function(e) {
        e.preventDefault();
        
        var itemName = $(this).data('item-name') || 'this item';
        var deleteUrl = $(this).attr('href');
        
        if (confirm('Are you sure you want to delete ' + itemName + '? This action cannot be undone.')) {
            window.location.href = deleteUrl;
        }
    });
    
    // Status toggle
    $('.status-toggle').change(function() {
        var itemId = $(this).data('item-id');
        var newStatus = $(this).is(':checked');
        var toggle = $(this);
        
        $.ajax({
            url: '/admin/toggle-status',
            method: 'POST',
            data: {
                id: itemId,
                status: newStatus,
                _token: $('meta[name="csrf-token"]').attr('content')
            },
            success: function(response) {
                if (response.success) {
                    showNotification('Status updated successfully', 'success');
                } else {
                    showNotification('Error updating status', 'error');
                    toggle.prop('checked', !newStatus);
                }
            },
            error: function() {
                showNotification('Error updating status', 'error');
                toggle.prop('checked', !newStatus);
            }
        });
    });
    
    // Data table search
    $('.data-table-search').on('keyup', function() {
        var value = $(this).val().toLowerCase();
        $('.data-table tbody tr').filter(function() {
            $(this).toggle($(this).text().toLowerCase().indexOf(value) > -1);
        });
    });
    
    // Auto-refresh dashboard stats
    if ($('.dashboard').length) {
        setInterval(function() {
            refreshDashboardStats();
        }, 30000); // Refresh every 30 seconds
    }
    
    // Chart initialization
    if (typeof Chart !== 'undefined') {
        initCharts();
    }
    
    // Rich text editor initialization
    if (typeof tinymce !== 'undefined') {
        tinymce.init({
            selector: '.rich-text-editor',
            height: 300,
            plugins: 'advlist autolink lists link image charmap print preview anchor searchreplace visualblocks code fullscreen insertdatetime media table paste code help wordcount',
            toolbar: 'undo redo | formatselect | bold italic backcolor | alignleft aligncenter alignright alignjustify | bullist numlist outdent indent | removeformat | help'
        });
    }
    
    // Date picker initialization
    $('.datepicker').datepicker({
        format: 'yyyy-mm-dd',
        autoclose: true,
        todayHighlight: true
    });
    
    // Time picker initialization
    $('.timepicker').timepicker({
        showMeridian: false,
        minuteStep: 15
    });
    
    // Color picker initialization
    $('.colorpicker').colorpicker();
    
    // Slug generation
    $('.slug-source').on('input', function() {
        var source = $(this).val();
        var slug = generateSlug(source);
        $('.slug-target').val(slug);
    });
    
    // Form validation
    $('form').submit(function(e) {
        var form = $(this);
        var isValid = true;
        
        // Clear previous error states
        form.find('.is-invalid').removeClass('is-invalid');
        form.find('.invalid-feedback').remove();
        
        // Validate required fields
        form.find('[required]').each(function() {
            var field = $(this);
            var value = field.val().trim();
            
            if (!value) {
                field.addClass('is-invalid');
                field.after('<div class="invalid-feedback">This field is required.</div>');
                isValid = false;
            }
        });
        
        // Validate email fields
        form.find('input[type="email"]').each(function() {
            var field = $(this);
            var value = field.val().trim();
            
            if (value && !isValidEmail(value)) {
                field.addClass('is-invalid');
                field.after('<div class="invalid-feedback">Please enter a valid email address.</div>');
                isValid = false;
            }
        });
        
        // Validate number fields
        form.find('input[type="number"]').each(function() {
            var field = $(this);
            var value = parseFloat(field.val());
            var min = parseFloat(field.attr('min'));
            var max = parseFloat(field.attr('max'));
            
            if (field.val() && (isNaN(value) || (min !== undefined && value < min) || (max !== undefined && value > max))) {
                field.addClass('is-invalid');
                field.after('<div class="invalid-feedback">Please enter a valid number.</div>');
                isValid = false;
            }
        });
        
        if (!isValid) {
            e.preventDefault();
            showNotification('Please fix the errors in the form', 'error');
        }
    });
});

// Utility Functions
function showNotification(message, type = 'info') {
    var alertClass = 'alert-info';
    var iconClass = 'fas fa-info-circle';
    
    switch(type) {
        case 'success':
            alertClass = 'alert-success';
            iconClass = 'fas fa-check-circle';
            break;
        case 'error':
            alertClass = 'alert-danger';
            iconClass = 'fas fa-exclamation-circle';
            break;
        case 'warning':
            alertClass = 'alert-warning';
            iconClass = 'fas fa-exclamation-triangle';
            break;
    }
    
    var notification = $(`
        <div class="alert ${alertClass} alert-dismissible fade show notification" style="position: fixed; top: 20px; right: 20px; z-index: 9999; min-width: 300px;">
            <i class="${iconClass} me-2"></i>${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        </div>
    `);
    
    $('body').append(notification);
    
    // Auto remove after 5 seconds
    setTimeout(function() {
        notification.alert('close');
    }, 5000);
}

function updateBulkActions() {
    var checkedItems = $('.item-checkbox:checked');
    var bulkActions = $('.bulk-actions');
    
    if (checkedItems.length > 0) {
        bulkActions.show();
        $('.bulk-count').text(checkedItems.length);
    } else {
        bulkActions.hide();
    }
}

function performBulkAction(action, itemIds) {
    $.ajax({
        url: '/admin/bulk-action',
        method: 'POST',
        data: {
            action: action,
            item_ids: itemIds,
            _token: $('meta[name="csrf-token"]').attr('content')
        },
        success: function(response) {
            if (response.success) {
                showNotification('Bulk action completed successfully', 'success');
                location.reload();
            } else {
                showNotification('Error performing bulk action', 'error');
            }
        },
        error: function() {
            showNotification('Error performing bulk action', 'error');
        }
    });
}

function refreshDashboardStats() {
    $.ajax({
        url: '/admin/dashboard/stats',
        method: 'GET',
        success: function(response) {
            if (response.success) {
                // Update stats cards
                $('.stats-card').each(function() {
                    var card = $(this);
                    var statType = card.data('stat-type');
                    if (response.data[statType]) {
                        card.find('.stats-content h3').text(response.data[statType]);
                    }
                });
            }
        }
    });
}

function initCharts() {
    // Sales chart
    if ($('#salesChart').length) {
        var ctx = document.getElementById('salesChart').getContext('2d');
        new Chart(ctx, {
            type: 'line',
            data: {
                labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
                datasets: [{
                    label: 'Sales',
                    data: [12, 19, 3, 5, 2, 3],
                    borderColor: 'rgb(75, 192, 192)',
                    tension: 0.1
                }]
            },
            options: {
                responsive: true,
                scales: {
                    y: {
                        beginAtZero: true
                    }
                }
            }
        });
    }
    
    // Orders chart
    if ($('#ordersChart').length) {
        var ctx = document.getElementById('ordersChart').getContext('2d');
        new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: ['Pending', 'Processing', 'Shipped', 'Delivered'],
                datasets: [{
                    data: [10, 20, 30, 40],
                    backgroundColor: [
                        '#ffc107',
                        '#17a2b8',
                        '#6f42c1',
                        '#28a745'
                    ]
                }]
            },
            options: {
                responsive: true
            }
        });
    }
}

function generateSlug(text) {
    return text
        .toLowerCase()
        .replace(/[^\w\s-]/g, '')
        .replace(/[\s_-]+/g, '-')
        .replace(/^-+|-+$/g, '');
}

function isValidEmail(email) {
    var emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
}

// Export functions for global use
window.adminUtils = {
    showNotification: showNotification,
    generateSlug: generateSlug,
    isValidEmail: isValidEmail
};
