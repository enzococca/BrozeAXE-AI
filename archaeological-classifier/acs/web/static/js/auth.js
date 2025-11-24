/**
 * Authentication Helper
 * ====================
 *
 * Global authentication utilities for BrozeAXE-AI web interface.
 * Include this file in pages that require authentication.
 */

const AuthHelper = {
    /**
     * Get stored authentication token
     */
    getToken() {
        return localStorage.getItem('token');
    },

    /**
     * Get stored user information
     */
    getUser() {
        const userStr = localStorage.getItem('user');
        return userStr ? JSON.parse(userStr) : null;
    },

    /**
     * Check if user is logged in
     */
    isLoggedIn() {
        return !!this.getToken();
    },

    /**
     * Check if user has specific role
     */
    hasRole(role) {
        const user = this.getUser();
        return user && user.role === role;
    },

    /**
     * Check if user has any of the specified roles
     */
    hasAnyRole(roles) {
        const user = this.getUser();
        return user && roles.includes(user.role);
    },

    /**
     * Verify token is still valid
     */
    async verifyToken() {
        const token = this.getToken();
        if (!token) return false;

        try {
            const response = await fetch('/api/auth/me', {
                headers: { 'Authorization': `Bearer ${token}` }
            });

            if (response.ok) {
                const data = await response.json();
                return data.status === 'success';
            }
            return false;
        } catch (error) {
            return false;
        }
    },

    /**
     * Logout user
     */
    async logout() {
        const token = this.getToken();
        if (token) {
            try {
                await fetch('/api/auth/logout', {
                    method: 'POST',
                    headers: { 'Authorization': `Bearer ${token}` }
                });
            } catch (error) {
                console.error('Logout error:', error);
            }
        }

        localStorage.removeItem('token');
        localStorage.removeItem('user');
        window.location.href = '/web/login';
    },

    /**
     * Redirect to login page
     */
    redirectToLogin() {
        window.location.href = '/web/login';
    },

    /**
     * Require authentication - redirect to login if not authenticated
     */
    async requireAuth() {
        if (!this.isLoggedIn()) {
            this.redirectToLogin();
            return false;
        }

        const valid = await this.verifyToken();
        if (!valid) {
            localStorage.removeItem('token');
            localStorage.removeItem('user');
            this.redirectToLogin();
            return false;
        }

        return true;
    },

    /**
     * Require specific role - redirect if user doesn't have it
     */
    async requireRole(roles) {
        const authenticated = await this.requireAuth();
        if (!authenticated) return false;

        if (!this.hasAnyRole(Array.isArray(roles) ? roles : [roles])) {
            alert('Access denied. Insufficient permissions.');
            window.location.href = '/web/dashboard';
            return false;
        }

        return true;
    },

    /**
     * Make authenticated fetch request
     */
    async fetch(url, options = {}) {
        const token = this.getToken();
        if (!token) {
            throw new Error('Not authenticated');
        }

        const headers = {
            ...options.headers,
            'Authorization': `Bearer ${token}`
        };

        const response = await fetch(url, { ...options, headers });

        // Handle auth errors
        if (response.status === 401) {
            this.redirectToLogin();
            throw new Error('Authentication required');
        }

        if (response.status === 403) {
            throw new Error('Access denied');
        }

        return response;
    },

    /**
     * Add logout button to navbar
     */
    addLogoutButton() {
        const user = this.getUser();
        if (!user) return;

        const navMenu = document.querySelector('.nav-menu');
        if (!navMenu) return;

        // Remove existing logout button if any
        const existing = document.getElementById('auth-logout-btn');
        if (existing) existing.remove();

        // Create logout button
        const logoutBtn = document.createElement('button');
        logoutBtn.id = 'auth-logout-btn';
        logoutBtn.innerHTML = '🚪 Logout';
        logoutBtn.style.cssText = `
            background: #e53e3e;
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 4px;
            cursor: pointer;
            font-size: 14px;
            font-weight: 500;
            margin-left: 10px;
        `;
        logoutBtn.onclick = () => this.logout();

        navMenu.insertBefore(logoutBtn, navMenu.firstChild);
    },

    /**
     * Display user info in navbar
     */
    showUserInfo() {
        const user = this.getUser();
        if (!user) return;

        const navBrand = document.querySelector('.nav-brand');
        if (!navBrand) return;

        // Remove existing user info
        const existing = document.getElementById('auth-user-info');
        if (existing) existing.remove();

        // Create user info display
        const userInfo = document.createElement('div');
        userInfo.id = 'auth-user-info';
        userInfo.style.cssText = `
            font-size: 12px;
            color: #666;
            margin-left: 15px;
        `;
        userInfo.innerHTML = `
            <span style="font-weight: 600;">${user.username}</span>
            <span style="background: #667eea; color: white; padding: 2px 8px; border-radius: 10px; margin-left: 5px; font-size: 10px;">
                ${user.role}
            </span>
        `;

        navBrand.appendChild(userInfo);
    }
};

// Auto-initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    // Add logout button and user info to protected pages
    if (AuthHelper.isLoggedIn() && window.location.pathname !== '/web/login') {
        AuthHelper.addLogoutButton();
        AuthHelper.showUserInfo();
    }
});

// Export for use in other scripts
if (typeof module !== 'undefined' && module.exports) {
    module.exports = AuthHelper;
}
