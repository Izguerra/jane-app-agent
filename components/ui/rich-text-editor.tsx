'use client';

import { useEditor, EditorContent } from '@tiptap/react';
import StarterKit from '@tiptap/starter-kit';
import Image from '@tiptap/extension-image';
import Link from '@tiptap/extension-link';
import Placeholder from '@tiptap/extension-placeholder';
import { useCallback, useEffect, useState } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import {
    Bold,
    Italic,
    Underline,
    List,
    ListOrdered,
    Link as LinkIcon,
    Image as ImageIcon,
    Undo,
    Redo,
    AlignLeft,
    Quote,
    Code,
    X
} from 'lucide-react';
import { cn } from '@/lib/utils';
import {
    Dialog,
    DialogContent,
    DialogHeader,
    DialogTitle,
    DialogFooter,
} from '@/components/ui/dialog';
import { Label } from '@/components/ui/label';

interface RichTextEditorProps {
    content: string;
    onChange: (html: string) => void;
    placeholder?: string;
    className?: string;
    onImageUpload?: (file: File) => Promise<string>;
}

export function RichTextEditor({
    content,
    onChange,
    placeholder = 'Write your email content here...',
    className,
    onImageUpload
}: RichTextEditorProps) {
    const [showImageDialog, setShowImageDialog] = useState(false);
    const [showLinkDialog, setShowLinkDialog] = useState(false);
    const [imageUrl, setImageUrl] = useState('');
    const [linkUrl, setLinkUrl] = useState('');
    const [isUploading, setIsUploading] = useState(false);

    const editor = useEditor({
        extensions: [
            StarterKit.configure({
                heading: {
                    levels: [1, 2, 3],
                },
            }),
            Image.configure({
                HTMLAttributes: {
                    class: 'max-w-full h-auto rounded-lg',
                },
            }),
            Link.configure({
                openOnClick: false,
                HTMLAttributes: {
                    class: 'text-blue-600 underline hover:text-blue-800',
                },
            }),
            Placeholder.configure({
                placeholder,
            }),
        ],
        content,
        onUpdate: ({ editor }) => {
            onChange(editor.getHTML());
        },
        editorProps: {
            attributes: {
                class: 'prose prose-sm max-w-none focus:outline-none min-h-[200px] p-4',
            },
        },
    });

    // Sync content changes from parent
    useEffect(() => {
        if (editor && content !== editor.getHTML()) {
            editor.commands.setContent(content);
        }
    }, [content, editor]);

    const addImage = useCallback(() => {
        if (imageUrl && editor) {
            editor.chain().focus().setImage({ src: imageUrl }).run();
            setImageUrl('');
            setShowImageDialog(false);
        }
    }, [editor, imageUrl]);

    const handleImageUpload = useCallback(async (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0];
        if (!file || !onImageUpload) return;

        setIsUploading(true);
        try {
            const url = await onImageUpload(file);
            if (editor) {
                editor.chain().focus().setImage({ src: url }).run();
            }
            setShowImageDialog(false);
        } catch (error) {
            console.error('Image upload failed:', error);
            alert('Failed to upload image');
        } finally {
            setIsUploading(false);
        }
    }, [editor, onImageUpload]);

    const addLink = useCallback(() => {
        if (linkUrl && editor) {
            editor.chain().focus().extendMarkRange('link').setLink({ href: linkUrl }).run();
            setLinkUrl('');
            setShowLinkDialog(false);
        }
    }, [editor, linkUrl]);

    const removeLink = useCallback(() => {
        if (editor) {
            editor.chain().focus().unsetLink().run();
        }
    }, [editor]);

    const insertVariable = useCallback((variable: string) => {
        if (editor) {
            editor.chain().focus().insertContent(`{{${variable}}}`).run();
        }
    }, [editor]);

    if (!editor) {
        return null;
    }

    return (
        <div className={cn('border rounded-lg overflow-hidden bg-background', className)}>
            {/* Toolbar */}
            <div className="flex flex-wrap items-center gap-1 p-2 border-b bg-muted/30">
                {/* Text Formatting */}
                <div className="flex items-center gap-0.5">
                    <ToolbarButton
                        onClick={() => editor.chain().focus().toggleBold().run()}
                        isActive={editor.isActive('bold')}
                        title="Bold"
                    >
                        <Bold className="h-4 w-4" />
                    </ToolbarButton>
                    <ToolbarButton
                        onClick={() => editor.chain().focus().toggleItalic().run()}
                        isActive={editor.isActive('italic')}
                        title="Italic"
                    >
                        <Italic className="h-4 w-4" />
                    </ToolbarButton>
                    <ToolbarButton
                        onClick={() => editor.chain().focus().toggleStrike().run()}
                        isActive={editor.isActive('strike')}
                        title="Strikethrough"
                    >
                        <span className="text-sm line-through font-medium">S</span>
                    </ToolbarButton>
                </div>

                <div className="w-px h-6 bg-border mx-1" />

                {/* Lists */}
                <div className="flex items-center gap-0.5">
                    <ToolbarButton
                        onClick={() => editor.chain().focus().toggleBulletList().run()}
                        isActive={editor.isActive('bulletList')}
                        title="Bullet List"
                    >
                        <List className="h-4 w-4" />
                    </ToolbarButton>
                    <ToolbarButton
                        onClick={() => editor.chain().focus().toggleOrderedList().run()}
                        isActive={editor.isActive('orderedList')}
                        title="Numbered List"
                    >
                        <ListOrdered className="h-4 w-4" />
                    </ToolbarButton>
                </div>

                <div className="w-px h-6 bg-border mx-1" />

                {/* Block Elements */}
                <div className="flex items-center gap-0.5">
                    <ToolbarButton
                        onClick={() => editor.chain().focus().toggleBlockquote().run()}
                        isActive={editor.isActive('blockquote')}
                        title="Quote"
                    >
                        <Quote className="h-4 w-4" />
                    </ToolbarButton>
                    <ToolbarButton
                        onClick={() => editor.chain().focus().toggleCodeBlock().run()}
                        isActive={editor.isActive('codeBlock')}
                        title="Code Block"
                    >
                        <Code className="h-4 w-4" />
                    </ToolbarButton>
                </div>

                <div className="w-px h-6 bg-border mx-1" />

                {/* Insert Elements */}
                <div className="flex items-center gap-0.5">
                    <ToolbarButton
                        onClick={() => setShowLinkDialog(true)}
                        isActive={editor.isActive('link')}
                        title="Insert Link"
                    >
                        <LinkIcon className="h-4 w-4" />
                    </ToolbarButton>
                    {editor.isActive('link') && (
                        <ToolbarButton
                            onClick={removeLink}
                            title="Remove Link"
                        >
                            <X className="h-4 w-4" />
                        </ToolbarButton>
                    )}
                    <ToolbarButton
                        onClick={() => setShowImageDialog(true)}
                        title="Insert Image"
                    >
                        <ImageIcon className="h-4 w-4" />
                    </ToolbarButton>
                </div>

                <div className="w-px h-6 bg-border mx-1" />

                {/* Undo/Redo */}
                <div className="flex items-center gap-0.5">
                    <ToolbarButton
                        onClick={() => editor.chain().focus().undo().run()}
                        disabled={!editor.can().undo()}
                        title="Undo"
                    >
                        <Undo className="h-4 w-4" />
                    </ToolbarButton>
                    <ToolbarButton
                        onClick={() => editor.chain().focus().redo().run()}
                        disabled={!editor.can().redo()}
                        title="Redo"
                    >
                        <Redo className="h-4 w-4" />
                    </ToolbarButton>
                </div>
            </div>

            {/* Variable Buttons */}
            <div className="flex items-center gap-2 px-3 py-2 border-b bg-muted/20">
                <span className="text-xs text-muted-foreground font-medium">Variables:</span>
                <div className="flex flex-wrap gap-1">
                    {['first_name', 'last_name', 'appointment_date'].map((variable) => (
                        <button
                            key={variable}
                            onClick={() => insertVariable(variable)}
                            className="text-xs bg-primary/10 text-primary px-2 py-0.5 rounded hover:bg-primary/20 transition-colors"
                        >
                            {`{{${variable}}}`}
                        </button>
                    ))}
                </div>
            </div>

            {/* Editor Content */}
            <EditorContent editor={editor} className="min-h-[200px]" />

            {/* Image Dialog */}
            <Dialog open={showImageDialog} onOpenChange={setShowImageDialog}>
                <DialogContent className="sm:max-w-md">
                    <DialogHeader>
                        <DialogTitle>Insert Image</DialogTitle>
                    </DialogHeader>
                    <div className="space-y-4 py-4">
                        <div className="space-y-2">
                            <Label>Image URL</Label>
                            <Input
                                placeholder="https://example.com/image.jpg"
                                value={imageUrl}
                                onChange={(e) => setImageUrl(e.target.value)}
                            />
                        </div>
                        {onImageUpload && (
                            <>
                                <div className="relative">
                                    <div className="absolute inset-0 flex items-center">
                                        <span className="w-full border-t" />
                                    </div>
                                    <div className="relative flex justify-center text-xs uppercase">
                                        <span className="bg-background px-2 text-muted-foreground">Or upload</span>
                                    </div>
                                </div>
                                <div className="space-y-2">
                                    <Label>Upload from computer</Label>
                                    <Input
                                        type="file"
                                        accept="image/*"
                                        onChange={handleImageUpload}
                                        disabled={isUploading}
                                    />
                                    {isUploading && (
                                        <p className="text-sm text-muted-foreground">Uploading...</p>
                                    )}
                                </div>
                            </>
                        )}
                    </div>
                    <DialogFooter>
                        <Button variant="outline" onClick={() => setShowImageDialog(false)}>
                            Cancel
                        </Button>
                        <Button onClick={addImage} disabled={!imageUrl}>
                            Insert
                        </Button>
                    </DialogFooter>
                </DialogContent>
            </Dialog>

            {/* Link Dialog */}
            <Dialog open={showLinkDialog} onOpenChange={setShowLinkDialog}>
                <DialogContent className="sm:max-w-md">
                    <DialogHeader>
                        <DialogTitle>Insert Link</DialogTitle>
                    </DialogHeader>
                    <div className="space-y-4 py-4">
                        <div className="space-y-2">
                            <Label>URL</Label>
                            <Input
                                placeholder="https://example.com"
                                value={linkUrl}
                                onChange={(e) => setLinkUrl(e.target.value)}
                            />
                        </div>
                    </div>
                    <DialogFooter>
                        <Button variant="outline" onClick={() => setShowLinkDialog(false)}>
                            Cancel
                        </Button>
                        <Button onClick={addLink} disabled={!linkUrl}>
                            Insert Link
                        </Button>
                    </DialogFooter>
                </DialogContent>
            </Dialog>
        </div>
    );
}

interface ToolbarButtonProps {
    onClick: () => void;
    isActive?: boolean;
    disabled?: boolean;
    title: string;
    children: React.ReactNode;
}

function ToolbarButton({ onClick, isActive, disabled, title, children }: ToolbarButtonProps) {
    return (
        <button
            onClick={onClick}
            disabled={disabled}
            title={title}
            className={cn(
                'h-8 w-8 flex items-center justify-center rounded transition-colors',
                isActive
                    ? 'bg-primary text-primary-foreground'
                    : 'hover:bg-muted text-foreground',
                disabled && 'opacity-50 cursor-not-allowed'
            )}
        >
            {children}
        </button>
    );
}
