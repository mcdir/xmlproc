
;;;; A simple elisp package for invoking xmlproc from within Emacs

; Put this in your .emacs to use this:
;
; (setq auto-mode-alist
;      (cons '(".*\\.xml\\'" . xml-mode)))
;
; (autoload 'xml-mode "xml-mode")

; For Emacs 19 compatibility
(when (not (fboundp 'kbd))
  (defmacro kbd (keys)
    (read-kbd-macro keys)))

(defun xml-mode()
  "Trivial XML mode with support for xmlproc validation."
  (interactive)
  (sgml-mode)
  (make-local-variable 'sgml-validate-command)
  (make-local-variable 'compilation-error-regexp-alist)

  (local-set-key (kbd "C-c C-v") #'compile)
  ; use C-x ` to jump between errors
  
  (setq compilation-error-regexp-alist 
	'(("\nE:\\([^:]+\\):\\([^:]+\\):\\([^:]+\\)" 1 2 3)))
  (setq compile-command
	(concat "python c:\\\\minedo~1\\\\programmering\\\\python\\\\xml\\\\xmlproc\\\\xvcmd.py "
		(file-name-nondirectory buffer-file-name)))
  (setq mode-name "XML"
	major-mode 'xml-mode))
