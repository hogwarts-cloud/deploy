resource "yandex_compute_instance_group" "group" {
  name               = "hogwarts-cloud-instance-group"
  service_account_id = yandex_iam_service_account.service_account.id
  depends_on         = [yandex_resourcemanager_folder_iam_member.editor]
  instance_template {
    platform_id = "standard-v3"

    name = "hogwarts-cloud-{instance.index}"
    hostname = "hogwarts-cloud-{instance.index}"
  
    resources {
      memory = 4
      cores  = 4
      core_fraction = 100
    }

    boot_disk {
      mode = "READ_WRITE"
      initialize_params {
        image_id = "fd82p04mkorgqovbtg3u" // debian 12
        size     = 30
      }
    }

    secondary_disk {
      mode = "READ_WRITE"
      initialize_params {
        size = 100
      }
    }
    
    network_interface {
      network_id = yandex_vpc_network.network.id
      subnet_ids = ["${yandex_vpc_subnet.subnet.id}"]
      nat = true
    }

    metadata = {
      ssh-keys = "debian:${file("~/.ssh/id_ed25519.pub")}"
    }
  }

  scale_policy {
    fixed_scale {
      size = 3
    }
  }

  allocation_policy {
    zones = ["ru-central1-a"]
  }

  deploy_policy {
    max_unavailable = 3
    max_expansion   = 0
  }
}
