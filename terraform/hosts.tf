resource "local_file" "hosts" {
  content = templatefile("${path.module}/templates/hosts.tpl",
    {
      bootstrap = element(yandex_compute_instance_group.group.instances, 0)
      members = slice(yandex_compute_instance_group.group.instances, 1, length(yandex_compute_instance_group.group.instances))
    }
  )
  filename        = "../ansible/inventory/hosts.ini"
  file_permission = "666"
}