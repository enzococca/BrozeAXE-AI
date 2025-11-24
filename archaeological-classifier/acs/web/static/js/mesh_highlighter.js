/**
 * Savignano Mesh Highlighter
 * ==========================
 *
 * Highlights morphometric features on 3D meshes (socket, flanges, blade).
 * Used for enhanced visualization during artifact comparison.
 */

class SavignanoMeshHighlighter {
    /**
     * Initialize highlighter for a Three.js mesh.
     *
     * @param {THREE.Mesh} mesh - The Three.js mesh to highlight
     * @param {Object} savignanoFeatures - Savignano morphometric features
     */
    constructor(mesh, savignanoFeatures) {
        this.mesh = mesh;
        this.features = savignanoFeatures || {};
        this.highlightedRegions = [];
        this.annotations = [];

        // Color scheme for highlighting
        this.colors = {
            socket: 0xff4444,      // Red for incavo
            flanges: 0x4444ff,     // Blue for margini rialzati
            blade: 0x44ff44,       // Green for tagliente
            butt: 0xffaa44,        // Orange for tallone
            default: 0x888888      // Gray default
        };
    }

    /**
     * Highlight all Savignano features on the mesh.
     */
    highlightAll() {
        if (this.features.incavo_presente) {
            this.highlightSocket();
        }

        if (this.features.margini_rialzati_presenti) {
            this.highlightFlanges();
        }

        if (this.features.tagliente_larghezza > 0) {
            this.highlightBlade();
        }

        if (this.features.tallone_larghezza > 0) {
            this.highlightButt();
        }
    }

    /**
     * Highlight socket (incavo) region in red.
     */
    highlightSocket() {
        // Socket is typically at the top (butt end) of the axe
        const geometry = this.mesh.geometry;
        const positions = geometry.attributes.position;
        const colors = new Float32Array(positions.count * 3);

        // Get bounding box to determine socket location
        geometry.computeBoundingBox();
        const bbox = geometry.getBoundingBox();
        const maxZ = bbox.max.z;
        const socketThreshold = maxZ - (this.features.incavo_profondita || 10);

        // Color vertices in socket region
        for (let i = 0; i < positions.count; i++) {
            const z = positions.getZ(i);

            if (z > socketThreshold) {
                // Inside socket region - red
                colors[i * 3] = 1.0;     // R
                colors[i * 3 + 1] = 0.27; // G
                colors[i * 3 + 2] = 0.27; // B
            } else {
                // Default color
                colors[i * 3] = 0.53;
                colors[i * 3 + 1] = 0.53;
                colors[i * 3 + 2] = 0.53;
            }
        }

        geometry.setAttribute('color', new THREE.BufferAttribute(colors, 3));
        this.mesh.material.vertexColors = true;
        this.mesh.material.needsUpdate = true;

        this.highlightedRegions.push({
            type: 'socket',
            color: this.colors.socket,
            threshold: socketThreshold
        });
    }

    /**
     * Highlight raised flanges (margini rialzati) in blue.
     */
    highlightFlanges() {
        // Flanges run along the body sides
        const geometry = this.mesh.geometry;
        const positions = geometry.attributes.position;

        geometry.computeBoundingBox();
        const bbox = geometry.getBoundingBox();

        // Flanges are along the sides (high X or low X values)
        const centerX = (bbox.max.x + bbox.min.x) / 2;
        const flangeWidth = (bbox.max.x - bbox.min.x) * 0.3;

        const colors = geometry.attributes.color || new Float32Array(positions.count * 3);

        for (let i = 0; i < positions.count; i++) {
            const x = positions.getX(i);
            const z = positions.getZ(i);

            // Check if on left or right flange
            if (Math.abs(x - centerX) > flangeWidth / 2) {
                // On flange - blue
                colors[i * 3] = 0.27;
                colors[i * 3 + 1] = 0.27;
                colors[i * 3 + 2] = 1.0;
            }
        }

        geometry.setAttribute('color', new THREE.BufferAttribute(colors, 3));
        this.mesh.material.vertexColors = true;
        this.mesh.material.needsUpdate = true;

        this.highlightedRegions.push({
            type: 'flanges',
            color: this.colors.flanges
        });
    }

    /**
     * Highlight blade (tagliente) region in green.
     */
    highlightBlade() {
        // Blade is at the opposite end from socket (bottom/cutting edge)
        const geometry = this.mesh.geometry;
        const positions = geometry.attributes.position;

        geometry.computeBoundingBox();
        const bbox = geometry.getBoundingBox();
        const minZ = bbox.min.z;
        const bladeThreshold = minZ + 20; // 20mm from bottom

        const colors = geometry.attributes.color || new Float32Array(positions.count * 3);

        for (let i = 0; i < positions.count; i++) {
            const z = positions.getZ(i);

            if (z < bladeThreshold) {
                // Blade region - green
                colors[i * 3] = 0.27;
                colors[i * 3 + 1] = 1.0;
                colors[i * 3 + 2] = 0.27;
            }
        }

        geometry.setAttribute('color', new THREE.BufferAttribute(colors, 3));
        this.mesh.material.vertexColors = true;
        this.mesh.material.needsUpdate = true;

        this.highlightedRegions.push({
            type: 'blade',
            color: this.colors.blade,
            threshold: bladeThreshold
        });
    }

    /**
     * Highlight butt (tallone) region in orange.
     */
    highlightButt() {
        const geometry = this.mesh.geometry;
        const positions = geometry.attributes.position;

        geometry.computeBoundingBox();
        const bbox = geometry.getBoundingBox();
        const maxZ = bbox.max.z;
        const buttThreshold = maxZ - 5; // Top 5mm

        const colors = geometry.attributes.color || new Float32Array(positions.count * 3);

        for (let i = 0; i < positions.count; i++) {
            const z = positions.getZ(i);

            if (z > buttThreshold) {
                // Butt region - orange
                colors[i * 3] = 1.0;
                colors[i * 3 + 1] = 0.67;
                colors[i * 3 + 2] = 0.27;
            }
        }

        geometry.setAttribute('color', new THREE.BufferAttribute(colors, 3));
        this.mesh.material.vertexColors = true;
        this.mesh.material.needsUpdate = true;

        this.highlightedRegions.push({
            type: 'butt',
            color: this.colors.butt,
            threshold: buttThreshold
        });
    }

    /**
     * Add measurement annotation to mesh.
     *
     * @param {string} label - Label text (e.g., "Tallone Width")
     * @param {number} value - Measurement value
     * @param {THREE.Vector3} position - 3D position for annotation
     * @param {HTMLElement} container - DOM container for annotation overlays
     */
    addAnnotation(label, value, position, container) {
        const annotation = {
            label,
            value,
            position,
            element: this._createAnnotationElement(label, value, position, container)
        };

        this.annotations.push(annotation);
        return annotation;
    }

    /**
     * Add all Savignano measurement annotations.
     *
     * @param {THREE.Camera} camera - Camera for projection
     * @param {HTMLElement} container - DOM container
     */
    addAllAnnotations(camera, container) {
        const geometry = this.mesh.geometry;
        geometry.computeBoundingBox();
        const bbox = geometry.getBoundingBox();

        // Socket depth annotation
        if (this.features.incavo_presente) {
            const socketPos = new THREE.Vector3(
                0,
                bbox.max.y,
                bbox.max.z - (this.features.incavo_profondita || 10) / 2
            );
            this.addAnnotation(
                'Incavo Depth',
                `${this.features.incavo_profondita.toFixed(1)}mm`,
                socketPos,
                container
            );
        }

        // Blade width annotation
        if (this.features.tagliente_larghezza) {
            const bladePos = new THREE.Vector3(
                bbox.max.x,
                0,
                bbox.min.z + 10
            );
            this.addAnnotation(
                'Tagliente Width',
                `${this.features.tagliente_larghezza.toFixed(1)}mm`,
                bladePos,
                container
            );
        }

        // Butt width annotation
        if (this.features.tallone_larghezza) {
            const buttPos = new THREE.Vector3(
                bbox.max.x,
                0,
                bbox.max.z - 5
            );
            this.addAnnotation(
                'Tallone Width',
                `${this.features.tallone_larghezza.toFixed(1)}mm`,
                buttPos,
                container
            );
        }
    }

    /**
     * Create annotation DOM element.
     * @private
     */
    _createAnnotationElement(label, value, position, container) {
        const div = document.createElement('div');
        div.className = 'mesh-annotation';
        div.innerHTML = `
            <div class="annotation-label">${label}</div>
            <div class="annotation-value">${value}</div>
        `;
        div.style.position = 'absolute';
        div.style.background = 'rgba(0, 0, 0, 0.7)';
        div.style.color = 'white';
        div.style.padding = '5px 10px';
        div.style.borderRadius = '4px';
        div.style.fontSize = '12px';
        div.style.pointerEvents = 'none';
        div.style.whiteSpace = 'nowrap';

        container.appendChild(div);
        return div;
    }

    /**
     * Update annotation positions based on camera view.
     *
     * @param {THREE.Camera} camera - Camera for projection
     */
    updateAnnotations(camera) {
        for (const annotation of this.annotations) {
            // Project 3D position to 2D screen coordinates
            const vector = annotation.position.clone();
            vector.project(camera);

            const x = (vector.x * 0.5 + 0.5) * window.innerWidth;
            const y = (-vector.y * 0.5 + 0.5) * window.innerHeight;

            annotation.element.style.left = `${x}px`;
            annotation.element.style.top = `${y}px`;

            // Hide if behind camera
            annotation.element.style.display = vector.z > 1 ? 'none' : 'block';
        }
    }

    /**
     * Clear all highlights and annotations.
     */
    clearHighlights() {
        // Reset mesh color
        if (this.mesh.geometry.attributes.color) {
            this.mesh.geometry.deleteAttribute('color');
        }

        this.mesh.material.vertexColors = false;
        this.mesh.material.needsUpdate = true;

        this.highlightedRegions = [];
    }

    /**
     * Clear all annotations.
     */
    clearAnnotations() {
        for (const annotation of this.annotations) {
            if (annotation.element && annotation.element.parentNode) {
                annotation.element.parentNode.removeChild(annotation.element);
            }
        }

        this.annotations = [];
    }

    /**
     * Toggle specific feature highlight on/off.
     *
     * @param {string} featureType - Type of feature ('socket', 'flanges', 'blade', 'butt')
     * @param {boolean} enabled - Enable or disable
     */
    toggleFeature(featureType, enabled) {
        if (enabled) {
            switch (featureType) {
                case 'socket':
                    this.highlightSocket();
                    break;
                case 'flanges':
                    this.highlightFlanges();
                    break;
                case 'blade':
                    this.highlightBlade();
                    break;
                case 'butt':
                    this.highlightButt();
                    break;
            }
        } else {
            // Re-highlight all except the disabled one
            this.clearHighlights();
            const activeRegions = this.highlightedRegions
                .map(r => r.type)
                .filter(t => t !== featureType);

            for (const type of activeRegions) {
                this.toggleFeature(type, true);
            }
        }
    }

    /**
     * Get legend for highlighted features.
     *
     * @returns {Array} Array of {type, color, label} objects
     */
    getLegend() {
        return this.highlightedRegions.map(region => ({
            type: region.type,
            color: region.color,
            label: this._getFeatureLabel(region.type)
        }));
    }

    /**
     * Get human-readable label for feature type.
     * @private
     */
    _getFeatureLabel(type) {
        const labels = {
            socket: 'Socket (Incavo)',
            flanges: 'Raised Flanges (Margini Rialzati)',
            blade: 'Blade (Tagliente)',
            butt: 'Butt (Tallone)'
        };

        return labels[type] || type;
    }
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = SavignanoMeshHighlighter;
}
