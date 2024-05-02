resource "yandex_iam_service_account" "service_account" {
  name = "hogwarts-cloud-sa"
}

resource "yandex_resourcemanager_folder_iam_member" "editor" {
  role      = "editor"
  folder_id = yandex_iam_service_account.service_account.folder_id
  member    = "serviceAccount:${yandex_iam_service_account.service_account.id}"
}