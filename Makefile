PACKAGE_VERSION=0.0.1
prefix=/usr

all:

clean:
	fixme

install:
	install -d -m 0755 "$(DESTDIR)/$(prefix)/sbin"
	install -m 0755 fpemud-portal "$(DESTDIR)/$(prefix)/sbin"

	install -d -m 0755 "$(DESTDIR)/$(prefix)/lib/fpemud-portal"
	cp -r lib/* "$(DESTDIR)/$(prefix)/lib/fpemud-portal"
	find "$(DESTDIR)/$(prefix)/lib/fpemud-portal" -type f | xargs chmod 644
	find "$(DESTDIR)/$(prefix)/lib/fpemud-portal" -type d | xargs chmod 755

	install -d -m 0755 "$(DESTDIR)/$(prefix)/share/fpemud-portal"
	cp -r share/* "$(DESTDIR)/$(prefix)/share/fpemud-portal"
	find "$(DESTDIR)/$(prefix)/share/fpemud-portal" -type f | xargs chmod 644
	find "$(DESTDIR)/$(prefix)/share/fpemud-portal" -type d | xargs chmod 755

	install -d -m 0755 "$(DESTDIR)/$(prefix)/lib/systemd/system"
	install -m 0644 data/fpemud-portal.service "$(DESTDIR)/$(prefix)/lib/systemd/system"

	install -d -m 0755 "$(DESTDIR)/var/fpemud-portal"

uninstall:
	rm -f "$(DESTDIR)/$(prefix)/sbin/fpemud-portal"
	rm -f "$(DESTDIR)/$(prefix)/lib/systemd/system/fpemud-portal.service"
	rm -rf "$(DESTDIR)/$(prefix)/lib/fpemud-portal"
	rm -rf "$(DESTDIR)/var/fpemud-portal"

.PHONY: all clean install uninstall
