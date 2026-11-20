// Cart Management
const Cart = {
    items: [],
    totalPrice: 0,

    // Initialize cart
    init: function() {
        // From API get cart data
        fetch('/api/cart')
            .then(response => response.json())
            .then(data => {
                this.items = data;
                this.updateCartCount();
                this.updateCartItems();
                this.calculateTotal();
            })
            .catch(error => console.error('Error loading cart:', error));
        
        // Add cart button event listener
        const cartButton = document.getElementById('cart-button');
        if (cartButton) {
            cartButton.addEventListener('click', () => this.toggleCart());
        }

        // Close cart event listener
        const cartClose = document.getElementById('cart-close');
        if (cartClose) {
            cartClose.addEventListener('click', () => this.toggleCart());
        }

        // Clear cart button event listener
        const clearCart = document.getElementById('clear-cart');
        if (clearCart) {
            clearCart.addEventListener('click', () => this.clearCart());
        }

        // Checkout button event listener
        const checkout = document.getElementById('checkout-button');
        if (checkout) {
            checkout.addEventListener('click', () => {
                window.location.href = '/delivery';
            });
        }

        // Listen for add to cart button
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('add-to-cart')) {
                const productId = e.target.dataset.id;
                this.addToCart(productId);
            }
        });

        // Bind cart overlay click event
        const cartOverlay = document.getElementById('cart-overlay');
        if (cartOverlay) {
            cartOverlay.addEventListener('click', (e) => {
                if (e.target === cartOverlay) {
                    this.toggleCart();
                }
            });
        }
    },

    // Toggle cart display
    toggleCart: function() {
        const cartOverlay = document.getElementById('cart-overlay');
        cartOverlay.classList.toggle('show');
    },

    // Add product to cart
    addToCart: function(productId) {
        fetch('/api/cart/add', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ id: productId })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                this.items = data.cart;
                this.updateCartCount();
                this.updateCartItems();
                this.calculateTotal();
                
                // Update button status
                const button = document.querySelector(`.add-to-cart[data-id="${productId}"]`);
                if (button) {
                    const originalText = button.textContent;
                    button.textContent = 'Added!';
                    setTimeout(() => {
                        button.textContent = originalText;
                    }, 1000);
                }
                
                // Update stock display for this product
                this.updateStockDisplay(productId, data.effective_stock);
            } else {
                // Show error message
                alert(data.message || 'Failed to add to cart');
                
                // If product is out of stock, disable the button
                if (data.message === 'Product out of stock' || data.message === 'Insufficient stock to add more') {
                    const buttons = document.querySelectorAll(`.add-to-cart[data-id="${productId}"]`);
                    buttons.forEach(btn => {
                        btn.disabled = true;
                        btn.textContent = 'Out of Stock';
                    });
                }
            }
        })
        .catch(error => console.error('Error adding to cart:', error));
    },

    // Update stock display for a specific product
    updateStockDisplay: function(productId, effectiveStock) {
        const stockElements = document.querySelectorAll(`.stock-status[data-id="${productId}"]`);
        
        stockElements.forEach(el => {
            if (effectiveStock <= 0) {
                el.classList.remove('in-stock');
                el.classList.add('out-of-stock');
                el.textContent = 'Out of Stock';
                
                // Disable all add to cart buttons for this product
                const buttons = document.querySelectorAll(`.add-to-cart[data-id="${productId}"]`);
                buttons.forEach(btn => {
                    btn.disabled = true;
                    btn.textContent = 'Out of Stock';
                });
            } else {
                el.classList.remove('out-of-stock');
                el.classList.add('in-stock');
                el.textContent = `In Stock (${effectiveStock} remaining)`;
            }
        });
    },

    // Update cart product quantity
    updateQuantity: function(productId, quantity) {
        fetch('/api/cart/update', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ id: productId, quantity: quantity })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                this.items = data.cart;
                this.updateCartCount();
                this.updateCartItems();
                this.calculateTotal();
                
                // Update stock display to reflect the change
                if (data.effective_stock !== undefined) {
                    this.updateStockDisplay(productId, data.effective_stock);
                }
            } else {
                // Show insufficient stock error
                alert(data.message || 'Failed to update cart');
                
                // If available stock information is provided, set quantity to maximum available
                if (data.available_stock !== undefined) {
                    const inputs = document.querySelectorAll(`.quantity-input[data-id="${productId}"]`);
                    inputs.forEach(input => {
                        input.value = data.available_stock;
                    });
                    
                    // Retry update with maximum available stock
                    if (data.available_stock > 0) {
                        this.updateQuantity(productId, data.available_stock);
                    }
                }
            }
        })
        .catch(error => console.error('Error updating cart:', error));
    },

    // Remove product from cart
    removeItem: function(productId) {
        this.updateQuantity(productId, 0);
    },

    // Clear cart
    clearCart: function() {
        fetch('/api/cart/clear', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                this.items = [];
                this.updateCartCount();
                this.updateCartItems();
                this.calculateTotal();
                
                // Update stock displays for all affected products
                if (data.stock_updates) {
                    for (const [productId, stockInfo] of Object.entries(data.stock_updates)) {
                        this.updateStockDisplay(productId, stockInfo.effective_stock);
                    }
                }
            }
        })
        .catch(error => console.error('Error clearing cart:', error));
    },

    // Update cart product quantity display
    updateCartCount: function() {
        const cartCount = document.getElementById('cart-count');
        if (cartCount) {
            const count = this.items.reduce((total, item) => total + item.quantity, 0);
            cartCount.textContent = count;
        }
    },

    // Update cart displayed products
    updateCartItems: function() {
        const cartItemsContainer = document.getElementById('cart-items');
        const emptyCart = document.getElementById('empty-cart');
        const checkoutButton = document.getElementById('checkout-button');
        
        if (!cartItemsContainer) return;
        
        if (this.items.length === 0) {
            cartItemsContainer.innerHTML = '';
            if (emptyCart) emptyCart.style.display = 'block';
            if (checkoutButton) checkoutButton.disabled = true;
            return;
        }
        
        if (emptyCart) emptyCart.style.display = 'none';
        if (checkoutButton) checkoutButton.disabled = false;
        
        let html = '';
        this.items.forEach(item => {
            html += `
                <li class="cart-item">
                    <img src="/static/images/${item.image}" alt="${item.name}" class="cart-item-image">
                    <div class="cart-item-details">
                        <div class="cart-item-name">${item.name}</div>
                        <div class="cart-item-price">$${item.price.toFixed(2)} per ${item.unit}</div>
                        <div class="cart-item-controls">
                            <button class="quantity-btn" onclick="Cart.decrementQuantity('${item.id}')">-</button>
                            <input type="number" class="quantity-input" value="${item.quantity}" min="1" 
                                   data-id="${item.id}" onchange="Cart.updateQuantity('${item.id}', this.value)">
                            <button class="quantity-btn" onclick="Cart.incrementQuantity('${item.id}')">+</button>
                            <button class="cart-item-remove" onclick="Cart.removeItem('${item.id}')">Delete</button>
                        </div>
                    </div>
                </li>
            `;
        });
        
        cartItemsContainer.innerHTML = html;
    },

    // Calculate total
    calculateTotal: function() {
        const totalElement = document.getElementById('cart-total-price');
        if (!totalElement) return;
        
        this.totalPrice = this.items.reduce((total, item) => {
            return total + (item.price * item.quantity);
        }, 0);
        
        totalElement.textContent = `$${this.totalPrice.toFixed(2)}`;
    },

    // Increase product quantity
    incrementQuantity: function(productId) {
        const item = this.items.find(item => item.id === productId);
        if (item) {
            this.updateQuantity(productId, item.quantity + 1);
        }
    },

    // Decrease product quantity
    decrementQuantity: function(productId) {
        const item = this.items.find(item => item.id === productId);
        if (item && item.quantity > 1) {
            this.updateQuantity(productId, item.quantity - 1);
        }
    }
};

// Category Management
const Categories = {
    init: function() {
        // Add category click event
        document.querySelectorAll('.category-title').forEach(category => {
            category.addEventListener('click', function() {
                // Toggle subcategory display
                const subcategories = this.nextElementSibling;
                if (subcategories) {
                    subcategories.classList.toggle('show');
                    
                    // Toggle arrow icon
                    const arrow = this.querySelector('.category-arrow');
                    if (arrow) {
                        arrow.textContent = subcategories.classList.contains('show') ? '▼' : '▶';
                    }
                }
            });
        });
    }
};

// Form Validation
const FormValidator = {
    init: function() {
        const form = document.getElementById('delivery-form');
        if (!form) return;
        
        form.addEventListener('submit', (e) => {
            e.preventDefault();
            
            if (this.validateForm()) {
                this.submitOrder();
            }
        });
        
        // Add input validation event listener
        form.querySelectorAll('input, select').forEach(input => {
            input.addEventListener('blur', () => {
                this.validateField(input);
            });
        });
    },
    
    validateForm: function() {
        const form = document.getElementById('delivery-form');
        let isValid = true;
        
        form.querySelectorAll('input, select').forEach(input => {
            if (!this.validateField(input)) {
                isValid = false;
            }
        });
        
        return isValid;
    },
    
    validateField: function(input) {
        const value = input.value.trim();
        let isValid = true;
        let errorMessage = '';
        
        // Required field validation
        if (input.hasAttribute('required') && value === '') {
            isValid = false;
            errorMessage = 'This field is required';
        } 
        // Email validation
        else if (input.type === 'email' && value !== '') {
            const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
            if (!emailRegex.test(value)) {
                isValid = false;
                errorMessage = 'Please enter a valid email address';
            }
        }
        // Phone number validation
        else if (input.id === 'phone' && value !== '') {
            // 澳大利亚电话号码格式验证，支持座机和手机号
            const phoneRegex = /^(?:\+?61|0)[2-478](?:[ -]?[0-9]){8}$/;
            if (!phoneRegex.test(value)) {
                isValid = false;
                errorMessage = '请输入有效的澳大利亚电话号码';
            }
        }
        
        // Show or hide error message
        const errorElement = document.getElementById(`${input.id}-error`);
        if (errorElement) {
            errorElement.textContent = errorMessage;
        }
        
        // Add or remove error style
        if (isValid) {
            input.classList.remove('error');
        } else {
            input.classList.add('error');
        }
        
        return isValid;
    },
    
    submitOrder: function() {
        const form = document.getElementById('delivery-form');
        const formData = {
            name: form.elements.name.value,
            email: form.elements.email.value,
            phone: form.elements.phone.value,
            street: form.elements.street.value,
            city: form.elements.city.value,
            state: form.elements.state.value
        };
        
        // Disable submit button while processing
        const submitBtn = form.querySelector('button[type="submit"]');
        if (submitBtn) {
            submitBtn.disabled = true;
            submitBtn.textContent = 'Processing...';
        }
        
        // 清除之前的错误提示
        const errorBox = document.getElementById('form-errors');
        if (errorBox) {
            errorBox.style.display = 'none';
            errorBox.textContent = '';
        }
        
        console.log('Submitting order with data:', formData);
        
        // Send order to server
        fetch('/api/order/submit', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(formData)
        })
        .then(response => {
            console.log('Response status:', response.status);
            return response.json();
        })
        .then(data => {
            console.log('Response data:', data);
            
            if (data.success) {
                // 在提交按钮上显示成功信息
                if (submitBtn) {
                    submitBtn.classList.add('success');
                    submitBtn.textContent = '订单提交成功!';
                }
                
                // 延迟重定向，让用户看到成功信息
                setTimeout(() => {
                    // Go to confirmation page
                    window.location.href = `/confirmation/${data.order.id}`;
                }, 1000);
            } else {
                // Show error message
                if (errorBox) {
                    let errorMessage = data.message || 'Failed to submit order';
                    
                    // If there are unavailable items, show details
                    if (data.unavailable_items && data.unavailable_items.length > 0) {
                        errorMessage += ':<br>';
                        data.unavailable_items.forEach(item => {
                            errorMessage += `- ${item.name}: Requested ${item.requested}, but only ${item.available} in stock`;
                            if (item.reason) {
                                errorMessage += ` (${item.reason})`;
                            }
                            errorMessage += '<br>';
                        });
                        errorMessage += '<br>Please return to your <a href="/cart">cart</a> to adjust quantities.';
                    }
                    
                    errorBox.innerHTML = errorMessage;
                    errorBox.style.display = 'block';
                    
                    // Scroll to error message
                    errorBox.scrollIntoView({ behavior: 'smooth' });
                }
                
                // Re-enable submit button
                if (submitBtn) {
                    submitBtn.disabled = false;
                    submitBtn.textContent = 'Place Order';
                }
            }
        })
        .catch(error => {
            console.error('Error submitting order:', error);
            
            // Re-enable submit button
            if (submitBtn) {
                submitBtn.disabled = false;
                submitBtn.textContent = 'Place Order';
            }
            
            // Show generic error message
            if (errorBox) {
                errorBox.textContent = 'An error occurred while processing your order. Please try again later.';
                errorBox.style.display = 'block';
                errorBox.scrollIntoView({ behavior: 'smooth' });
            }
        });
    }
};

// Initialize after page load
document.addEventListener('DOMContentLoaded', function() {
    Cart.init();
    Categories.init();
    FormValidator.init();
}); 