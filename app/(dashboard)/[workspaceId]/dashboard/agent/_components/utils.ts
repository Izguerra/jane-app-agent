
// File validation helper
export const validateImageFile = async (
    file: File,
    options: {
        maxSizeMB: number;
        allowedTypes: string[];
        maxWidth?: number;
        maxHeight?: number;
        recommendedWidth?: number;
        recommendedHeight?: number;
    }
): Promise<{ valid: boolean; error?: string; warning?: string }> => {
    // Check file type
    if (!options.allowedTypes.includes(file.type)) {
        return {
            valid: false,
            error: `Invalid file type. Please upload ${options.allowedTypes.map(t => t.split('/')[1].toUpperCase()).join(', ')} files only.`
        };
    }

    // Check file size
    const maxSizeBytes = options.maxSizeMB * 1024 * 1024;
    if (file.size > maxSizeBytes) {
        return {
            valid: false,
            error: `File size must be less than ${options.maxSizeMB}MB. Current size: ${(file.size / 1024 / 1024).toFixed(2)}MB`
        };
    }

    // Check image dimensions (if not SVG)
    if (file.type !== 'image/svg+xml' && (options.maxWidth || options.maxHeight || options.recommendedWidth || options.recommendedHeight)) {
        return new Promise((resolve) => {
            const img = new Image();
            img.onload = () => {
                URL.revokeObjectURL(img.src);

                // Check max dimensions
                if (options.maxWidth && img.width > options.maxWidth) {
                    resolve({
                        valid: false,
                        error: `Image width must be less than ${options.maxWidth}px. Current: ${img.width}px`
                    });
                    return;
                }
                if (options.maxHeight && img.height > options.maxHeight) {
                    resolve({
                        valid: false,
                        error: `Image height must be less than ${options.maxHeight}px. Current: ${img.height}px`
                    });
                    return;
                }

                // Check recommended dimensions (warning only)
                let warning;
                if (options.recommendedWidth && options.recommendedHeight) {
                    if (img.width !== options.recommendedWidth || img.height !== options.recommendedHeight) {
                        warning = `Recommended size is ${options.recommendedWidth}x${options.recommendedHeight}px. Current: ${img.width}x${img.height}px`;
                    }
                }

                resolve({ valid: true, warning });
            };
            img.onerror = () => {
                URL.revokeObjectURL(img.src);
                resolve({ valid: false, error: 'Failed to load image. Please try another file.' });
            };
            img.src = URL.createObjectURL(file);
        });
    }

    return { valid: true };
};

export const validateDocumentFile = (
    file: File,
    options: {
        maxSizeMB: number;
        allowedTypes: string[];
    }
): { valid: boolean; error?: string } => {
    if (!options.allowedTypes.includes(file.type)) {
        return {
            valid: false,
            error: `Invalid file type. Please upload ${options.allowedTypes.map(t => t.split('/')[1].toUpperCase()).join(', ')} files only.`
        };
    }

    const maxSizeBytes = options.maxSizeMB * 1024 * 1024;
    if (file.size > maxSizeBytes) {
        return {
            valid: false,
            error: `File size must be less than ${options.maxSizeMB}MB. Current size: ${(file.size / 1024 / 1024).toFixed(2)}MB`
        };
    }

    return { valid: true };
};

export const safeParse = (value: any, fallback: any) => {
    if (!value) return fallback;
    if (typeof value !== 'string') return value;
    try {
        return JSON.parse(value);
    } catch (e) {
        console.warn("Failed to parse JSON:", value, e);
        return fallback;
    }
};
