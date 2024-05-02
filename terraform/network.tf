resource "yandex_vpc_network" "network" {
  name = "hogwarts-cloud-network"
}

resource "yandex_vpc_subnet" "subnet" {
  name           = "hogwarts-cloud-subnet"
  zone           = "ru-central1-a"
  network_id     = yandex_vpc_network.network.id
  v4_cidr_blocks = ["192.168.0.0/16"]
}