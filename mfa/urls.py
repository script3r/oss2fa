"""mfa URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.10/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import url
from django.contrib import admin

from challenge.views import ChallengeList, ChallengeDetailView, ChallengeCompletionView
from enrollment.views import EnrollmentList, EnrollmentDetail, EnrollmentCompletion, EnrollmentDeviceSelection
from tenants.views import IntegrationClientAuthDecision, TenantsListView, TenantIntegrationListView

urlpatterns = [
    url(r'^integration/clients/auth',
        IntegrationClientAuthDecision.as_view(), name='client-auth'),

    url(r'^integration/challenges/(?P<pk>[0-9]+)/complete',
        ChallengeCompletionView.as_view(), name='challenge-complete'),
    url(r'^integration/challenges/(?P<pk>[0-9]+)',
        ChallengeDetailView.as_view(), name='challenge-detail'),
    url(r'^integration/challenges', ChallengeList.as_view(), name='challenge-list'),

    url(r'^integration/enrollments/(?P<pk>[0-9]+)/complete',
        EnrollmentCompletion.as_view(), name='enrollment-complete'),
    url(r'^integration/enrollments/(?P<pk>[0-9]+)/device-selection', EnrollmentDeviceSelection.as_view(),
        name='enrollment-device-selection'),
    url(r'^integration/enrollments/(?P<pk>[0-9]+)',
        EnrollmentDetail.as_view(), name='enrollment-detail'),
    url(r'^integration/enrollments',
        EnrollmentList.as_view(), name='enrollment-list'),

    url(r'^tenants/integrations', TenantIntegrationListView.as_view(),
        name='tenant-integration-list'),
    url(r'^tenants', TenantsListView.as_view(), name='tenant-list'),

    url(r'^admin/', admin.site.urls),
]
