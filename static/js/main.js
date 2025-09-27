// Main JavaScript for MVC Shopping

$(document).ready(function() {
    // Initialize tooltips
    $('[data-bs-toggle="tooltip"]').tooltip();
    
    // Initialize popovers
    $('[data-bs-toggle="popover"]').popover();
    
    // Smooth scrolling for anchor links
    $('a[href^="#"]').on('click', function(event) {
        var target = $(this.getAttribute('href'));
        if (target.length) {
            event.preventDefault();
            $('html, body').stop().animate({
                scrollTop: target.offset().top - 100
            }, 1000);
        }
    });
    
    // Add to cart functionality
    $('.add-to-cart').click(function(e) {
        e.preventDefault();
        
        var productId = $(this).data('product-id');
        var quantity = parseInt($('#quantity').val()) || 1;
        var button = $(this);
        var originalText = button.html();
        
        // Disable button and show loading
        button.prop('disabled', true).html('<i class="fas fa-spinner fa-spin me-2"></i>Adding...');
        
        $.ajax({
            url: '/api/cart/add',
            method: 'POST',
            contentType: 'application/json',
            data: JSON.stringify({
                product_id: productId,
                quantity: quantity
            }),
            success: function(response) {
                if (response.success) {
                    // Update cart count
                    $('#cart-count').text(response.cart_count);
                    
                    // Show success message
                    showNotification('Item added to cart successfully!', 'success');
                    
                    // Update button
                    button.html('<i class="fas fa-check me-2"></i>Added!');
                    button.removeClass('btn-primary').addClass('btn-success');
                    
                    // Reset button after 2 seconds
                    setTimeout(function() {
                        button.html(originalText);
                        button.removeClass('btn-success').addClass('btn-primary');
                        button.prop('disabled', false);
                    }, 2000);
                } else {
                    showNotification(response.message || 'Error adding item to cart', 'error');
                    button.html(originalText).prop('disabled', false);
                }
            },
            error: function(xhr) {
                var response = JSON.parse(xhr.responseText);
                showNotification(response.message || 'Error adding item to cart', 'error');
                button.html(originalText).prop('disabled', false);
            }
        });
    });
    
    // Quantity controls
    $('.quantity-controls .btn').click(function() {
        var input = $(this).siblings('input[type="number"]');
        var currentVal = parseInt(input.val());
        var maxVal = parseInt(input.attr('max')) || 999;
        var minVal = parseInt(input.attr('min')) || 1;
        
        if ($(this).hasClass('increase-qty')) {
            if (currentVal < maxVal) {
                input.val(currentVal + 1);
            }
        } else if ($(this).hasClass('decrease-qty')) {
            if (currentVal > minVal) {
                input.val(currentVal - 1);
            }
        }
        
        // Trigger change event
        input.trigger('change');
    });
    
    // Product image gallery
    $('.thumbnail-image').click(function() {
        var mainImageSrc = $(this).data('main-src');
        if (mainImageSrc) {
            $('#main-product-image').attr('src', mainImageSrc);
            $('.thumbnail-image').removeClass('active');
            $(this).addClass('active');
        }
    });
    
    // Search functionality
    $('#search-form').submit(function(e) {
        var query = $('#search-input').val().trim();
        if (!query) {
            e.preventDefault();
            showNotification('Please enter a search term', 'warning');
        }
    });
    
    // Newsletter subscription
    $('.newsletter-form').submit(function(e) {
        e.preventDefault();
        
        var email = $(this).find('input[type="email"]').val();
        var button = $(this).find('button[type="submit"]');
        var originalText = button.html();
        
        if (!isValidEmail(email)) {
            showNotification('Please enter a valid email address', 'error');
            return;
        }
        
        button.prop('disabled', true).html('<i class="fas fa-spinner fa-spin me-2"></i>Subscribing...');
        
        // Simulate API call
        setTimeout(function() {
            showNotification('Thank you for subscribing to our newsletter!', 'success');
            button.html(originalText).prop('disabled', false);
            $('.newsletter-form input[type="email"]').val('');
        }, 2000);
    });
    
    // Coupon code validation
    $('#apply-coupon').click(function() {
        var couponCode = $('#coupon-code').val().trim();
        var button = $(this);
        var originalText = button.html();
        
        if (!couponCode) {
            showNotification('Please enter a coupon code', 'warning');
            return;
        }
        
        button.prop('disabled', true).html('<i class="fas fa-spinner fa-spin me-2"></i>Applying...');
        
        $.ajax({
            url: '/api/validate-coupon',
            method: 'POST',
            contentType: 'application/json',
            data: JSON.stringify({
                code: couponCode
            }),
            success: function(response) {
                if (response.success) {
                    showNotification('Coupon applied successfully! Discount: $' + response.discount.toFixed(2), 'success');
                    // Update cart total with discount
                    updateCartTotal(response.discount);
                } else {
                    showNotification(response.message, 'error');
                }
                button.html(originalText).prop('disabled', false);
            },
            error: function(xhr) {
                var response = JSON.parse(xhr.responseText);
                showNotification(response.message || 'Error applying coupon', 'error');
                button.html(originalText).prop('disabled', false);
            }
        });
    });
    
    // Wishlist functionality
    $('.wishlist-btn').click(function(e) {
        e.preventDefault();
        
        var productId = $(this).data('product-id');
        var button = $(this);
        var icon = button.find('i');
        
        if (icon.hasClass('far')) {
            // Add to wishlist
            icon.removeClass('far').addClass('fas');
            button.addClass('text-danger');
            showNotification('Added to wishlist', 'success');
        } else {
            // Remove from wishlist
            icon.removeClass('fas').addClass('far');
            button.removeClass('text-danger');
            showNotification('Removed from wishlist', 'info');
        }
    });
    
    // Product comparison
    $('.compare-btn').click(function(e) {
        e.preventDefault();
        
        var productId = $(this).data('product-id');
        var button = $(this);
        
        // Add to comparison list
        if (!button.hasClass('active')) {
            button.addClass('active').html('<i class="fas fa-check me-2"></i>Added');
            showNotification('Product added to comparison', 'success');
        } else {
            button.removeClass('active').html('<i class="fas fa-balance-scale me-2"></i>Compare');
            showNotification('Product removed from comparison', 'info');
        }
    });
    
    // Lazy loading for images
    if ('IntersectionObserver' in window) {
        const imageObserver = new IntersectionObserver((entries, observer) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const img = entry.target;
                    img.src = img.dataset.src;
                    img.classList.remove('lazy');
                    imageObserver.unobserve(img);
                }
            });
        });
        
        document.querySelectorAll('img[data-src]').forEach(img => {
            imageObserver.observe(img);
        });
    }
    
    // Back to top button
    var backToTop = $('<button class="btn btn-primary back-to-top" style="position: fixed; bottom: 20px; right: 20px; z-index: 1000; display: none; border-radius: 50%; width: 50px; height: 50px;"><i class="fas fa-arrow-up"></i></button>');
    $('body').append(backToTop);
    
    $(window).scroll(function() {
        if ($(this).scrollTop() > 300) {
            backToTop.fadeIn();
        } else {
            backToTop.fadeOut();
        }
    });
    
    backToTop.click(function() {
        $('html, body').animate({scrollTop: 0}, 800);
    });
    
    // Initialize cart count
    updateCartCount();
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

function isValidEmail(email) {
    var emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
}

function updateCartCount() {
    $.ajax({
        url: '/api/cart/count',
        method: 'GET',
        success: function(response) {
            $('#cart-count').text(response.count);
        }
    });
}

function updateCartTotal(discount) {
    // This would update the cart total with the discount
    // Implementation depends on your cart structure
    console.log('Cart total updated with discount:', discount);
}

// Product filtering
function filterProducts() {
    var category = $('input[name="category"]:checked').val();
    var minPrice = $('#min-price').val();
    var maxPrice = $('#max-price').val();
    var search = $('#search-input').val();
    
    var url = new URL(window.location);
    
    if (category) url.searchParams.set('category', category);
    else url.searchParams.delete('category');
    
    if (minPrice) url.searchParams.set('min_price', minPrice);
    else url.searchParams.delete('min_price');
    
    if (maxPrice) url.searchParams.set('max_price', maxPrice);
    else url.searchParams.delete('max_price');
    
    if (search) url.searchParams.set('search', search);
    else url.searchParams.delete('search');
    
    window.location.href = url.toString();
}

// Price range slider
function initPriceRangeSlider() {
    var minPrice = 0;
    var maxPrice = 1000;
    
    // This would initialize a range slider
    // Implementation depends on your preferred slider library
}

// Product quick view
function showQuickView(productId) {
    // This would show a modal with product details
    // Implementation depends on your modal structure
    console.log('Quick view for product:', productId);
}

// Share functionality
function shareProduct(url, title) {
    if (navigator.share) {
        navigator.share({
            title: title,
            url: url
        });
    } else {
        // Fallback to copying URL to clipboard
        navigator.clipboard.writeText(url).then(function() {
            showNotification('Product URL copied to clipboard', 'success');
        });
    }
}

// Initialize share buttons
$('.share-btn').click(function(e) {
    e.preventDefault();
    var url = window.location.href;
    var title = document.title;
    shareProduct(url, title);
});
