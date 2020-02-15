# -*- mode: ruby -*-
# vi: set ft=ruby ts=2 sw=2 expandtab :

PROJECT = "allansimon_mock_zendesk"
UID = Process.euid

DOCKER_ENV = {
  'HOST_USER_UID' => UID,

  'MOCK_ZENDESK_API_KEY'=> 'dummy_zendesk_api_key',
  'MOCK_ZENDESK_USERNAME'=> 'dummy_zendesk_user',
  'MOCK_ZENDESK_PORT '=> '8084',
}

ENV['VAGRANT_NO_PARALLEL'] = 'yes'
ENV['VAGRANT_DEFAULT_PROVIDER'] = 'docker'
Vagrant.configure(2) do |config|

  config.ssh.insert_key = false
  config.vm.define "dev", primary: true do |app|
    app.vm.provider "docker" do |d|
      d.image = "allansimon/allan-docker-dev-python"
      d.name = "#{PROJECT}_dev"
      d.has_ssh = true
      d.env = DOCKER_ENV
    end
    app.ssh.username = "vagrant"

    # so that we can git clone from within the docker
    app.vm.provision "file", source: "~/.ssh/id_rsa", destination: ".ssh/id_rsa"

    app.vm.provision "install_everything", type: "shell", privileged: false  do |s|
      s.inline = "
        cd /vagrant

        python3.7 -m venv /tmp/venv
        source /tmp/venv/bin/activate
        pip install wheel

        echo 'source /tmp/venv/bin/activate' >> /home/vagrant/.zshrc
        echo 'cd /vagrant' >> /home/vagrant/.zshrc
      "
    end
  end
end
