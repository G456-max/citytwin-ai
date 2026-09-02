/**
 * Unified drag-and-swipe compare slider controller for CityTwin AI.
 */
class SplitSliderController {
    constructor(containerId, overlayId, handleId) {
        this.container = document.getElementById(containerId);
        this.overlay = document.getElementById(overlayId);
        this.handle = document.getElementById(handleId);
        this.isDragging = false;
    }

    init() {
        if (!this.container || !this.overlay || !this.handle) {
            console.error("Split slider elements missing during initialization.");
            return;
        }

        const dragStart = (e) => {
            this.isDragging = true;
            e.preventDefault();
        };

        const dragEnd = () => {
            this.isDragging = false;
        };

        const dragMove = (e) => {
            if (!this.isDragging) return;
            
            const rect = this.container.getBoundingClientRect();
            const clientX = e.touches ? e.touches[0].clientX : e.clientX;
            const xOffset = clientX - rect.left;
            
            // Calculate percentage
            const percentage = (xOffset / rect.width) * 100;
            this.setPosition(percentage);
        };

        // Desktop listeners
        this.handle.addEventListener('mousedown', dragStart);
        window.addEventListener('mouseup', dragEnd);
        window.addEventListener('mousemove', dragMove);

        // Mobile touch listeners
        this.handle.addEventListener('touchstart', dragStart);
        window.addEventListener('touchend', dragEnd);
        window.addEventListener('touchmove', dragMove, { passive: false });

        // Set default midpoint
        this.setPosition(50);
    }

    setPosition(percentage) {
        const clippedPercentage = Math.max(0, Math.min(100, percentage));
        this.overlay.style.width = `${clippedPercentage}%`;
        this.handle.style.left = `${clippedPercentage}%`;
    }
}

// Attach to global window object
window.SplitSliderController = SplitSliderController;
