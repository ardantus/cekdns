import time
import dns.resolver
import dns.reversename
import socket
from django.shortcuts import render


def make_result(name, status, info):
    return {"name": name, "status": status, "info": info}


def reverse_lookup(ip):
    try:
        rev = dns.reversename.from_address(ip)
        return str(dns.resolver.resolve(rev, "PTR")[0])
    except:
        return "No PTR"


def get_all_ips(hostname):
    try:
        infos = socket.getaddrinfo(hostname, None)
        return sorted(set([info[4][0] for info in infos]))
    except:
        return []


def calculate_health_score(result):
    total = 0
    passed = 0
    for section in result.values():
        for test in section:
            total += 1
            if test["status"] == "OK":
                passed += 1
    return round((passed / total) * 100, 1) if total > 0 else 0


def check_spf(domain):
    try:
        txt_records = dns.resolver.resolve(domain, 'TXT')
        for r in txt_records:
            if str(r).lower().startswith('"v=spf1'):
                return make_result("SPF Record", "OK", str(r).strip('"'))
        return make_result("SPF Record", "ERROR", "No SPF record found")
    except Exception as e:
        return make_result("SPF Record", "ERROR", str(e))


def check_dkim(domain):
    selector = "default"
    dkim_domain = f"{selector}._domainkey.{domain}"
    try:
        txt_records = dns.resolver.resolve(dkim_domain, 'TXT')
        return make_result("DKIM Record", "OK", "\n".join([str(r).strip('"') for r in txt_records]))
    except Exception as e:
        return make_result("DKIM Record", "ERROR", f"{dkim_domain}: {str(e)}")


def check_dmarc(domain):
    dmarc_domain = f"_dmarc.{domain}"
    try:
        txt_records = dns.resolver.resolve(dmarc_domain, 'TXT')
        return make_result("DMARC Record", "OK", str(txt_records[0]).strip('"'))
    except Exception as e:
        return make_result("DMARC Record", "ERROR", f"{dmarc_domain}: {str(e)}")


def dns_lookup(domain):
    result = {}
    for key in ["Parent", "NS", "SOA", "MX", "WWW", "DNSSEC", "Email"]:
        result[key] = []

    resolver = dns.resolver.Resolver()
    resolver.timeout = 5
    resolver.lifetime = 5
    resolver.nameservers = ['8.8.8.8', '1.1.1.1']

    # Parent NS
    try:
        ns_rrset = resolver.resolve(domain, 'NS')
        ttl = ns_rrset.rrset.ttl
        ns_info = []
        for r in ns_rrset:
            ns = r.to_text()
            ips = get_all_ips(ns)
            ip_lines = "\n".join([f"{ns} -> {ip}" for ip in ips]) or f"{ns} -> unresolved"
            ns_info.append(f"{ip_lines} [TTL={ttl}]")
        result["Parent"].append(make_result("DNS NS records", "OK", "\n\n".join(ns_info)))
    except Exception as e:
        result["Parent"].append(make_result("DNS NS records", "ERROR", str(e)))

    # DNSSEC
    try:
        ds_records = dns.resolver.resolve(domain, 'DS')
        info = "\n".join([str(r) for r in ds_records])
        result["DNSSEC"].append(make_result("DNSSEC Records", "OK", info))
    except dns.resolver.NoAnswer:
        result["DNSSEC"].append(make_result("DNSSEC Records", "ERROR", "No DS record found"))
    except Exception as e:
        result["DNSSEC"].append(make_result("DNSSEC Records", "ERROR", str(e)))

    # NS glue records
    try:
        ns_data = resolver.resolve(domain, 'NS')
        ttl = ns_data.rrset.ttl
        glue_records = []
        for r in ns_data:
            ns = r.to_text()
            ips = get_all_ips(ns)
            ip_lines = "\n".join([f"{ns} -> {ip}" for ip in ips]) or f"{ns} -> unresolved"
            glue_records.append(f"{ip_lines} [TTL={ttl}]")
        result["NS"].append(make_result("Glue for NS records", "OK", "\n\n".join(glue_records)))
    except Exception as e:
        result["NS"].append(make_result("Glue for NS records", "ERROR", str(e)))

    # Recursive test
    try:
        allow_recursion = []
        for r in resolver.resolve(domain, 'NS'):
            ns = r.to_text()
            try:
                ip = socket.gethostbyname(ns)
                test_resolver = dns.resolver.Resolver(configure=False)
                test_resolver.nameservers = [ip]
                try:
                    test_resolver.resolve("example.com", "A")
                    allow_recursion.append(f"{ns} ({ip}) allows recursion")
                except:
                    pass
            except:
                continue
        if not allow_recursion:
            result["NS"].append(make_result("Recursive Queries", "OK", "All NS do not allow recursion"))
        else:
            result["NS"].append(make_result("Recursive Queries", "ERROR", "\n".join(allow_recursion)))
    except Exception as e:
        result["NS"].append(make_result("Recursive Queries", "ERROR", str(e)))

    # SOA
    try:
        soa = resolver.resolve(domain, 'SOA')[0]
        info = (
            f"Primary NS     : {soa.mname}\n"
            f"Responsible     : {soa.rname}\n"
            f"Serial          : {soa.serial}\n"
            f"Refresh         : {soa.refresh}\n"
            f"Retry           : {soa.retry}\n"
            f"Expire          : {soa.expire}\n"
            f"Minimum TTL     : {soa.minimum}"
        )
        result["SOA"].append(make_result("SOA Record", "OK", info))
    except Exception as e:
        result["SOA"].append(make_result("SOA Record", "ERROR", str(e)))

    # MX
    try:
        mx_records = resolver.resolve(domain, 'MX')
        entries = []
        for r in mx_records:
            hostname = str(r.exchange).rstrip('.')
            try:
                ips = get_all_ips(hostname)
                ptrs = [f"{ip} -> {reverse_lookup(ip)}" for ip in ips]
                ptr_info = "\n".join(ptrs)
                entries.append(f"{hostname} (prio {r.preference})\n{ptr_info}")
            except Exception as e:
                entries.append(f"{hostname} (prio {r.preference})\nError: {e}")
        result["MX"].append(make_result("MX Records", "OK", "\n\n".join(entries)))
    except Exception as e:
        result["MX"].append(make_result("MX Records", "ERROR", str(e)))

    # WWW A record
    try:
        a_records = resolver.resolve("www." + domain, 'A')
        records = [r.address for r in a_records]
        result["WWW"].append(make_result("WWW A Record", "OK", "\n".join(records)))
    except Exception as e:
        result["WWW"].append(make_result("WWW A Record", "ERROR", str(e)))

    # WWW CNAME record
    try:
        cname_records = resolver.resolve("www." + domain, 'CNAME')
        result["WWW"].append(make_result("WWW CNAME", "OK", "\n".join([r.to_text() for r in cname_records])))
    except:
        result["WWW"].append(make_result("WWW CNAME", "ERROR", "No CNAME for www"))

    # Email security
    result["Email"].append(check_spf(domain))
    result["Email"].append(check_dkim(domain))
    result["Email"].append(check_dmarc(domain))

    return result


def index(request):
    if request.method == "POST":
        domain = request.POST.get("domain", "").strip()
        if domain:
            start = time.time()
            result = dns_lookup(domain)
            elapsed = time.time() - start
            score = calculate_health_score(result)
            return render(request, "checker/result.html", {
                "domain": domain,
                "result": result,
                "elapsed_time": elapsed,
                "health_score": score
            })
    return render(request, "checker/index.html")

def domain_check(request, domain):
    domain = domain.strip()
    if domain:
        start = time.time()
        result = dns_lookup(domain)
        elapsed = time.time() - start
        score = calculate_health_score(result)
        return render(request, "checker/result.html", {
            "domain": domain,
            "result": result,
            "elapsed_time": elapsed,
            "health_score": score
        })
    return render(request, "checker/index.html")