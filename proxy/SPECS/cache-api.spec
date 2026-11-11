Name:           cache-api
Version:        0.1.0 
Release:        1%{?dist}
Summary:        Flask caching proxy API
BuildArch:	noarch

License:        Proprietary
Source0:        cache-api.py
Source1:	config-api.yaml
Source2:	cache-api.service

BuildRequires:  systemd
Requires:	python3
Requires:	python3-flask	
Requires:	python3-redis
Requires:	python3-pyyaml
Requires:	python3-requests
	


%description
A Flask proxy application with Valkey caching and Go backend integration.

%install
install -D -m 0644 %{SOURCE0} %{buildroot}%{_libexecdir}/cache-api/cache-api.py
install -D -m 0644 %{SOURCE1} %{buildroot}%{_sysconfdir}/cache-api/config.yaml
install -D -m 0644 %{SOURCE2} %{buildroot}%{_unitdir}/cache-api.service

%files
%dir %{_libexecdir}/cache-api
%dir %{_sysconfdir}/cache-api

%{_libexecdir}/cache-api/cache-api.py
%config(noreplace) %{_sysconfdir}/cache-api/config.yaml
%{_unitdir}/cache-api.service

%post
%systemd_post cache-api.service

%preun
%systemd_preun cache-api.service

%postun
%systemd_postun cache-api.service

%changelog
* Tue Nov 10 2026 max
- 
