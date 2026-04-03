from django.utils.deprecation import MiddlewareMixin
from .audit_models import AuditLog

class AuditMiddleware(MiddlewareMixin):
    """Log all requests to sensitive areas for FERPA compliance"""
    
    SENSITIVE_PATHS = ['repair', 'loaner', 'student', 'tickets', 'inventory']
    
    def process_request(self, request):
        if request.user.is_authenticated:
            path = request.path.lower()
            if any(sensitive in path for sensitive in self.SENSITIVE_PATHS):
                request._audit_log = True
                
    def process_response(self, request, response):
        if hasattr(request, '_audit_log') and request.user.is_authenticated:
            action = {
                'GET': 'VIEW',
                'POST': 'CREATE',
                'PUT': 'UPDATE',
                'PATCH': 'UPDATE',
                'DELETE': 'DELETE',
            }.get(request.method, 'VIEW')
            
            AuditLog.objects.create(
                user=request.user,
                username=request.user.username,
                action=action,
                ip_address=self._get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', '')[:255],
                object_repr=f"Path: {request.path}",
            )
        
        return response
    
    def _get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        return x_forwarded_for.split(',')[0] if x_forwarded_for else request.META.get('REMOTE_ADDR')