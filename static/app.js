/**
 * GLOBAL DATAROOM - Client-Side JavaScript
 * Fibonacci-Web-Designer © 2026
 */

// Global utilities
window.showModal = function(title, content) {
  const overlay = document.createElement('div');
  overlay.className = 'modal-overlay active';
  overlay.innerHTML = `
    <div class="modal">
      <div class="modal-header">
        <h3 class="modal-title">${title}</h3>
        <button class="modal-close" onclick="this.closest('.modal-overlay').remove()">×</button>
      </div>
      <div class="modal-body">
        ${content}
      </div>
    </div>
  `;

  overlay.addEventListener('click', (e) => {
    if (e.target === overlay) {
      overlay.remove();
    }
  });

  document.body.appendChild(overlay);
};

// Toast notification system
window.showToast = function(message, type = 'info') {
  const toast = document.createElement('div');
  toast.className = `alert alert-${type}`;
  toast.style.position = 'fixed';
  toast.style.top = '20px';
  toast.style.right = '20px';
  toast.style.zIndex = '9999';
  toast.style.minWidth = '300px';
  toast.style.animation = 'slideInRight 0.4s ease';
  toast.innerHTML = message;

  document.body.appendChild(toast);

  setTimeout(() => {
    toast.style.animation = 'slideInRight 0.4s ease reverse';
    setTimeout(() => toast.remove(), 400);
  }, 3000);
};

// Format number with commas
window.formatNumber = function(num) {
  return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ',');
};

// Format date
window.formatDate = function(dateString) {
  const date = new Date(dateString);
  return date.toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric'
  });
};

// Truncate text
window.truncate = function(text, length = 60) {
  return text.length > length ? text.substring(0, length) + '...' : text;
};

// Copy to clipboard
window.copyToClipboard = function(text) {
  navigator.clipboard.writeText(text).then(() => {
    showToast('✅ Copied to clipboard', 'success');
  }).catch(() => {
    showToast('❌ Failed to copy', 'error');
  });
};

// Debounce function
window.debounce = function(func, wait) {
  let timeout;
  return function executedFunction(...args) {
    const later = () => {
      clearTimeout(timeout);
      func(...args);
    };
    clearTimeout(timeout);
    timeout = setTimeout(later, wait);
  };
};

// API helper
window.api = {
  async get(endpoint) {
    try {
      const response = await fetch(endpoint);
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      return await response.json();
    } catch (error) {
      console.error('API GET error:', error);
      throw error;
    }
  },

  async post(endpoint, data) {
    try {
      const response = await fetch(endpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(data)
      });
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      return await response.json();
    } catch (error) {
      console.error('API POST error:', error);
      throw error;
    }
  },

  async upload(endpoint, formData) {
    try {
      const response = await fetch(endpoint, {
        method: 'POST',
        body: formData
      });
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      return await response.json();
    } catch (error) {
      console.error('API UPLOAD error:', error);
      throw error;
    }
  }
};

// Protocol badge color helper
window.getProtocolBadgeClass = function(type) {
  const types = {
    'code': 'badge-code',
    'config': 'badge-config',
    'agent': 'badge-agent',
    'document': 'badge-document'
  };
  return types[type] || 'badge-document';
};

// Blockchain hash formatter
window.formatHash = function(hash, length = 16) {
  if (!hash) return 'N/A';
  return hash.substring(0, length) + '...';
};

// Loading state helper
window.setLoading = function(element, isLoading, originalContent = '') {
  if (isLoading) {
    element.dataset.originalContent = element.innerHTML;
    element.disabled = true;
    element.innerHTML = '<span class="spinner"></span><span>Loading...</span>';
  } else {
    element.disabled = false;
    element.innerHTML = element.dataset.originalContent || originalContent;
  }
};

// Smooth scroll to element
window.scrollToElement = function(selector, offset = 0) {
  const element = document.querySelector(selector);
  if (element) {
    const top = element.getBoundingClientRect().top + window.pageYOffset - offset;
    window.scrollTo({
      top: top,
      behavior: 'smooth'
    });
  }
};

// Check if element is in viewport
window.isInViewport = function(element) {
  const rect = element.getBoundingClientRect();
  return (
    rect.top >= 0 &&
    rect.left >= 0 &&
    rect.bottom <= (window.innerHeight || document.documentElement.clientHeight) &&
    rect.right <= (window.innerWidth || document.documentElement.clientWidth)
  );
};

// Animate on scroll
window.animateOnScroll = function() {
  const elements = document.querySelectorAll('[data-aos]');
  elements.forEach(element => {
    if (isInViewport(element)) {
      element.classList.add('aos-animate');
    }
  });
};

// Initialize animations
document.addEventListener('DOMContentLoaded', () => {
  // Animate elements on scroll
  window.addEventListener('scroll', debounce(animateOnScroll, 100));
  animateOnScroll();

  // Add smooth reveal to cards
  const cards = document.querySelectorAll('.card');
  cards.forEach((card, index) => {
    card.style.animationDelay = `${index * 0.1}s`;
  });

  // Add hover effects to stat cards
  const statCards = document.querySelectorAll('.stat-card');
  statCards.forEach((card, index) => {
    card.style.animationDelay = `${index * 0.1}s`;
  });

  // Console easter egg
  console.log('%c🔐 CARBON ROOM [6]', 'font-size: 24px; font-weight: bold; color: #2D7DD2;');
  console.log('%cCreator IP Registry - Pressure Creates. Structure Enables.', 'font-size: 14px; color: #666;');
  console.log('%cDesigned by Fibonacci-Web-Designer', 'font-size: 12px; color: #2D7DD2;');
});

// Keyboard shortcuts
document.addEventListener('keydown', (e) => {
  // Ctrl/Cmd + K for search
  if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
    e.preventDefault();
    const searchInput = document.querySelector('.search-input');
    if (searchInput) {
      searchInput.focus();
      searchInput.select();
    }
  }

  // Escape to close modals
  if (e.key === 'Escape') {
    const modals = document.querySelectorAll('.modal-overlay.active');
    modals.forEach(modal => modal.classList.remove('active'));
  }
});

// Performance monitoring
if (window.performance) {
  window.addEventListener('load', () => {
    const perfData = window.performance.timing;
    const pageLoadTime = perfData.loadEventEnd - perfData.navigationStart;
    console.log(`%c⚡ Page loaded in ${pageLoadTime}ms`, 'color: #2D7DD2;');
  });
}

// Handle offline/online status
window.addEventListener('offline', () => {
  showToast('⚠️ You are offline. Some features may not work.', 'error');
});

window.addEventListener('online', () => {
  showToast('✅ Back online!', 'success');
});

// Service worker registration (for future PWA support)
if ('serviceWorker' in navigator) {
  // Uncomment when service worker is ready
  // navigator.serviceWorker.register('/sw.js').then(() => {
  //   console.log('Service Worker registered');
  // });
}

// Export for use in other scripts
window.DataRoom = {
  api,
  showModal,
  showToast,
  formatNumber,
  formatDate,
  formatHash,
  truncate,
  copyToClipboard,
  debounce,
  getProtocolBadgeClass,
  setLoading,
  scrollToElement,
  isInViewport,
  animateOnScroll
};
