[bootstrap]
${bootstrap.name} ansible_host=${bootstrap.network_interface.0.nat_ip_address} internal_host=${bootstrap.network_interface.0.ip_address}

[members]
%{ for member in members ~}
${member.name} ansible_host=${member.network_interface.0.nat_ip_address} internal_host=${member.network_interface.0.ip_address}
%{ endfor ~}
