"""
Email utility module for Pasargad Prints
Handles all email sending functionality with retry logic and templating
"""

import logging
import time
from typing import List, Optional, Dict, Any
from django.core.mail import EmailMultiAlternatives, get_connection
from django.template.loader import render_to_string
from django.conf import settings
from django.utils.html import strip_tags
from django.db import models
from django.utils import timezone
import json

logger = logging.getLogger(__name__)


class EmailQueue(models.Model):
    """Model to store emails in queue for retry logic"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('sent', 'Sent'),
        ('failed', 'Failed'),
    ]
    
    to_email = models.EmailField()
    from_email = models.EmailField(default=settings.DEFAULT_FROM_EMAIL)
    subject = models.CharField(max_length=255)
    html_content = models.TextField()
    plain_content = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    attempts = models.IntegerField(default=0)
    max_attempts = models.IntegerField(default=3)
    created_at = models.DateTimeField(auto_now_add=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    last_error = models.TextField(blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'created_at']),
        ]
    
    def __str__(self):
        return f"{self.to_email} - {self.subject} ({self.status})"


class EmailService:
    """
    Email service for sending emails with retry logic and template support
    """
    
    def __init__(self):
        self.from_email = settings.DEFAULT_FROM_EMAIL
        self.max_retries = 3
        self.retry_delay = 5  # seconds
        
    def send_email(
        self,
        to_email: str,
        subject: str,
        template_name: str,
        context: Dict[str, Any],
        from_email: Optional[str] = None,
        attachments: Optional[List[tuple]] = None,
        queue_on_failure: bool = True
    ) -> bool:
        """
        Send an email using templates with retry logic
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            template_name: Name of the template (without extension)
            context: Context dictionary for template rendering
            from_email: Sender email (optional)
            attachments: List of (filename, content, mimetype) tuples
            queue_on_failure: Whether to queue email if sending fails
            
        Returns:
            bool: True if email was sent successfully, False otherwise
        """
        try:
            # Add default context
            default_context = {
                'company_name': 'Pasargad Prints',
                'company_url': settings.FRONTEND_URL,
                'support_email': 'support@pasargadprints.com',
                'current_year': timezone.now().year,
            }
            context.update(default_context)
            
            # Render templates
            html_content = render_to_string(f'emails/{template_name}.html', context)
            plain_content = render_to_string(f'emails/{template_name}.txt', context)
            
            # Send with retry logic
            return self._send_with_retry(
                to_email=to_email,
                subject=subject,
                html_content=html_content,
                plain_content=plain_content,
                from_email=from_email or self.from_email,
                attachments=attachments,
                queue_on_failure=queue_on_failure,
                metadata={'template': template_name, 'context': context}
            )
            
        except Exception as e:
            logger.error(f"Error preparing email: {str(e)}")
            if queue_on_failure:
                self._queue_email(
                    to_email=to_email,
                    subject=subject,
                    html_content="",
                    plain_content=f"Error rendering template: {str(e)}",
                    from_email=from_email or self.from_email,
                    metadata={'template': template_name, 'error': str(e)}
                )
            return False
    
    def _send_with_retry(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        plain_content: str,
        from_email: str,
        attachments: Optional[List[tuple]] = None,
        queue_on_failure: bool = True,
        metadata: Optional[Dict] = None
    ) -> bool:
        """
        Send email with retry logic
        """
        attempts = 0
        last_error = None
        
        while attempts < self.max_retries:
            try:
                # Create email message
                email = EmailMultiAlternatives(
                    subject=subject,
                    body=plain_content,
                    from_email=from_email,
                    to=[to_email]
                )
                email.attach_alternative(html_content, "text/html")
                
                # Add attachments if any
                if attachments:
                    for filename, content, mimetype in attachments:
                        email.attach(filename, content, mimetype)
                
                # Send email
                email.send(fail_silently=False)
                
                logger.info(f"Email sent successfully to {to_email}")
                return True
                
            except Exception as e:
                attempts += 1
                last_error = str(e)
                logger.warning(f"Email send attempt {attempts} failed: {last_error}")
                
                if attempts < self.max_retries:
                    time.sleep(self.retry_delay)
        
        # All retries failed
        logger.error(f"Failed to send email to {to_email} after {attempts} attempts")
        
        if queue_on_failure:
            self._queue_email(
                to_email=to_email,
                subject=subject,
                html_content=html_content,
                plain_content=plain_content,
                from_email=from_email,
                last_error=last_error,
                metadata=metadata
            )
        
        return False
    
    def _queue_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        plain_content: str,
        from_email: str,
        last_error: Optional[str] = None,
        metadata: Optional[Dict] = None
    ):
        """
        Queue email for later processing
        """
        try:
            EmailQueue.objects.create(
                to_email=to_email,
                subject=subject,
                html_content=html_content,
                plain_content=plain_content,
                from_email=from_email,
                last_error=last_error or "",
                metadata=metadata or {}
            )
            logger.info(f"Email queued for {to_email}")
        except Exception as e:
            logger.error(f"Failed to queue email: {str(e)}")
    
    def process_email_queue(self, batch_size: int = 10):
        """
        Process pending emails from the queue
        """
        pending_emails = EmailQueue.objects.filter(
            status='pending',
            attempts__lt=models.F('max_attempts')
        ).order_by('created_at')[:batch_size]
        
        for email_item in pending_emails:
            email_item.attempts += 1
            
            try:
                # Create and send email
                email = EmailMultiAlternatives(
                    subject=email_item.subject,
                    body=email_item.plain_content,
                    from_email=email_item.from_email,
                    to=[email_item.to_email]
                )
                email.attach_alternative(email_item.html_content, "text/html")
                email.send(fail_silently=False)
                
                # Mark as sent
                email_item.status = 'sent'
                email_item.sent_at = timezone.now()
                email_item.save()
                
                logger.info(f"Queued email sent to {email_item.to_email}")
                
            except Exception as e:
                email_item.last_error = str(e)
                
                if email_item.attempts >= email_item.max_attempts:
                    email_item.status = 'failed'
                    logger.error(f"Queued email failed permanently: {email_item.to_email}")
                
                email_item.save()
    
    def send_order_confirmation(self, order):
        """
        Send order confirmation email
        """
        # Determine recipient email and name
        if order.user:
            to_email = order.user.email
            customer_name = order.user.get_full_name() or order.user.username
        else:
            # Guest order - use billing email
            to_email = order.billing_email or order.shipping_email
            customer_name = order.billing_name or order.shipping_name or 'Guest'
        
        if not to_email:
            logger.error(f"No email address found for order {order.order_number}")
            return False
        
        context = {
            'order': order,
            'order_number': order.order_number,
            'customer_name': customer_name,
            'order_items': order.items.all(),
            'total_amount': order.total_amount,
            'created_at': order.created_at,
            'frontend_url': settings.FRONTEND_URL,
            'is_guest': order.user is None,
            'tracking_url': f"{settings.FRONTEND_URL}/orders/track/{order.order_number}",
        }
        
        return self.send_email(
            to_email=to_email,
            subject=f"Order Confirmation - #{order.order_number}",
            template_name='order_confirmation',
            context=context
        )
    
    def send_order_status_update(self, order, old_status):
        """
        Send order status update email
        """
        # Determine recipient email and name
        if order.user:
            to_email = order.user.email
            customer_name = order.user.get_full_name() or order.user.username
        else:
            to_email = order.billing_email or order.shipping_email
            customer_name = order.billing_name or order.shipping_name or 'Guest'
        
        if not to_email:
            logger.error(f"No email address found for order {order.order_number}")
            return False
        
        context = {
            'order': order,
            'order_number': order.order_number,
            'customer_name': customer_name,
            'old_status': old_status,
            'new_status': order.status,
            'status_changed_at': timezone.now(),
            'frontend_url': settings.FRONTEND_URL,
            'is_guest': order.user is None,
            'tracking_url': f"{settings.FRONTEND_URL}/orders/track/{order.order_number}",
        }
        
        # Special handling for shipped status
        if order.status == 'shipped':
            template_name = 'order_shipped'
            subject = f"Your Order #{order.order_number} Has Been Shipped!"
            context['tracking_number'] = order.tracking_number
            context['estimated_delivery'] = order.estimated_delivery
        else:
            template_name = 'order_status_update'
            subject = f"Order Status Update - #{order.order_number}"
        
        return self.send_email(
            to_email=to_email,
            subject=subject,
            template_name=template_name,
            context=context
        )
    
    def send_password_reset(self, user, reset_token):
        """
        Send password reset email
        """
        context = {
            'user': user,
            'username': user.username,
            'reset_token': reset_token,
            'reset_url': f"{settings.FRONTEND_URL}/reset-password?token={reset_token}",
            'frontend_url': settings.FRONTEND_URL,
        }
        
        return self.send_email(
            to_email=user.email,
            subject="Password Reset Request - Pasargad Prints",
            template_name='password_reset',
            context=context
        )
    
    def send_test_email(self, to_email: str):
        """
        Send a test email to verify email configuration
        """
        context = {
            'test_time': timezone.now(),
            'recipient': to_email,
        }
        
        # Create simple test content if template doesn't exist
        html_content = f"""
        <html>
            <body>
                <h2>Test Email from Pasargad Prints</h2>
                <p>This is a test email sent at {context['test_time']}</p>
                <p>If you received this email, your email configuration is working correctly!</p>
                <hr>
                <p><small>Pasargad Prints - Premium Persian Miniature Art</small></p>
            </body>
        </html>
        """
        plain_content = strip_tags(html_content)
        
        return self._send_with_retry(
            to_email=to_email,
            subject="Test Email - Pasargad Prints",
            html_content=html_content,
            plain_content=plain_content,
            from_email=self.from_email,
            queue_on_failure=False
        )


    def send_order_shipped_notification(self, order):
        """
        Send order shipped notification email
        """
        # Determine recipient
        if order.user:
            to_email = order.user.email
            customer_name = order.user.get_full_name() or order.user.username
        else:
            to_email = order.billing_email or order.shipping_email
            customer_name = order.billing_name or order.shipping_name or 'Guest'
        
        if not to_email:
            logger.error(f"No email address found for order {order.order_number}")
            return False
        
        context = {
            'order': order,
            'order_number': order.order_number,
            'customer_name': customer_name,
            'tracking_number': order.tracking_number,
            'estimated_delivery': order.estimated_delivery,
            'shipping_address': {
                'name': order.shipping_name,
                'address': order.shipping_address,
                'city': order.shipping_city,
                'state': order.shipping_state,
                'postal_code': order.shipping_postal_code,
                'country': order.shipping_country,
            },
            'order_items': order.items.all(),
            'frontend_url': settings.FRONTEND_URL,
            'is_guest': order.user is None,
            'tracking_url': f"{settings.FRONTEND_URL}/orders/track/{order.order_number}",
        }
        
        return self.send_email(
            to_email=to_email,
            subject=f"Your Order #{order.order_number} Has Been Shipped!",
            template_name='order_shipped',
            context=context
        )
    
    def send_order_delivered_notification(self, order):
        """
        Send order delivered notification email
        """
        # Determine recipient
        if order.user:
            to_email = order.user.email
            customer_name = order.user.get_full_name() or order.user.username
        else:
            to_email = order.billing_email or order.shipping_email
            customer_name = order.billing_name or order.shipping_name or 'Guest'
        
        if not to_email:
            logger.error(f"No email address found for order {order.order_number}")
            return False
        
        context = {
            'order': order,
            'order_number': order.order_number,
            'customer_name': customer_name,
            'delivered_at': order.delivered_at or timezone.now(),
            'order_items': order.items.all(),
            'total_amount': order.total_amount,
            'frontend_url': settings.FRONTEND_URL,
            'is_guest': order.user is None,
            'review_url': f"{settings.FRONTEND_URL}/orders/{order.order_number}/review",
        }
        
        return self.send_email(
            to_email=to_email,
            subject=f"Your Order #{order.order_number} Has Been Delivered!",
            template_name='order_delivered',
            context=context
        )
    
    def send_guest_order_receipt(self, order):
        """
        Send a receipt email to guest customers with tracking information
        """
        to_email = order.billing_email or order.shipping_email
        if not to_email:
            logger.error(f"No email address found for guest order {order.order_number}")
            return False
        
        context = {
            'order': order,
            'order_number': order.order_number,
            'customer_name': order.billing_name or order.shipping_name or 'Guest',
            'order_items': order.items.all(),
            'subtotal': order.subtotal,
            'tax_amount': order.tax_amount,
            'shipping_cost': order.shipping_cost,
            'total_amount': order.total_amount,
            'created_at': order.created_at,
            'frontend_url': settings.FRONTEND_URL,
            'tracking_url': f"{settings.FRONTEND_URL}/orders/track/guest?order={order.order_number}&email={to_email}",
            'billing_address': {
                'name': order.billing_name,
                'address': order.billing_address,
                'city': order.billing_city,
                'state': order.billing_state,
                'postal_code': order.billing_postal_code,
                'country': order.billing_country,
            },
            'shipping_address': {
                'name': order.shipping_name,
                'address': order.shipping_address,
                'city': order.shipping_city,
                'state': order.shipping_state,
                'postal_code': order.shipping_postal_code,
                'country': order.shipping_country,
            },
        }
        
        return self.send_email(
            to_email=to_email,
            subject=f"Your Pasargad Prints Order #{order.order_number}",
            template_name='guest_order_receipt',
            context=context
        )


# Create a singleton instance
email_service = EmailService()