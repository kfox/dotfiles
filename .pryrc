begin
  require 'awesome_print'

  # Pry.config.print = proc do |output, value|
  #   Pry::Helpers::BaseHelpers.stagger_output("=> #{value.ai}", output)
  # end

  module AwesomePrint
    class Inspector
      alias_method :old_printable, :printable
      private
      def printable(object)
        if object.class.to_s.downcase.include?("activerecord_relation")
          return :activerecord_relation
        end
        if object.class.to_s.downcase.include?("collectionproxy")
          return :activerecord_relation
        end
        old_printable(object)
      end
    end
  end

  AwesomePrint.pry!
rescue LoadError => err
  puts "Try: gem install awesome_print"
end

# begin
#   require 'hirb'
#
#   Hirb.enable output: {
#     user: {
#       options: {
#         fields: %w{id email}
#       }
#     }
#   }
#   old_print = Pry.config.print
#   Pry.config.print = proc do |output, value|
#     Hirb::View.view_or_page_output(value) || old_print.call(output, value)
#   end
#
#   # Dirty hack to support in-session Hirb.disable/enable
#   # Hirb::View.instance_eval do
#   #   def enable_output_method
#   #     @output_method = true
#   #     Pry.config.print = proc do |output, value|
#   #       Hirb::View.view_or_page_output(value) || Pry::DEFAULT_PRINT.call(output, value)
#   #     end
#   #   end
#   #
#   #   def disable_output_method
#   #     Pry.config.print = proc { |output, value| Pry::DEFAULT_PRINT.call(output, value) }
#   #     @output_method = nil
#   #   end
#   # end
#   #
#   # Hirb.enable
# rescue LoadError => err
#   puts "Try: gem install hirb"
# end

Pry.config.editor      = "mvim"
Pry.config.auto_indent = true
Pry.config.color       = true

default_command_set = Pry::CommandSet.new do

  command "copy", "Copy argument to the clip-board" do |str|
     IO.popen('pbcopy', 'w') { |f| f << str.to_s }
  end

  command "clear" do
    system 'clear'
    if ENV['RAILS_ENV']
      output.puts "Rails Environment: " + ENV['RAILS_ENV']
    end
  end

  command "sql", "Send sql over AR." do |query|
    if ENV['RAILS_ENV'] || defined?(Rails)
      ap ActiveRecord::Base.connection.select_all(query)
    else
      ap "Pry did not require the environment, try `pconsole`"
    end
  end

  command "caller_method" do |depth|
    depth = depth.to_i || 1
    if /^(.+?):(\d+)(?::in `(.*)')?/ =~ caller(depth+1).first
      file   = Regexp.last_match[1]
      line   = Regexp.last_match[2].to_i
      method = Regexp.last_match[3]
      output.puts [file, line, method]
    end
  end

end

if defined?(Rails) && Rails.env
  require 'logger'

  ActiveRecord::Base.logger = Logger.new(STDOUT)
  ActiveRecord::Base.clear_active_connections!

  class Class
    def core_ext
      self.instance_methods.map do |m|
        [m, self.instance_method(m).source_location]
      end.select { |m| m[1] && m[1][0] =~/activesupport/ }.map { |m| m[0] }.sort
    end
  end

  class Object
    def local_methods
      (methods - Object.instance_methods).sort
    end
  end
end

Pry.config.commands.import default_command_set
Pry.config.should_load_plugins = false

# Pry.prompt = [
#   proc { |obj, nest_level, _| "#{RUBY_VERSION} (#{obj}):#{nest_level} > " },
#   proc { |obj, nest_level, _| "#{RUBY_VERSION} (#{obj}):#{nest_level} * " }
# ]

Pry.prompt = [
  proc { |target_self, nest_level, pry|
    "[#{pry.input_array.size}]\001\e[0;37m\002 #{Pry.config.prompt_name} #{RUBY_VERSION}\001\e[0m\002(\001\e[0;33m\002#{Pry.view_clip(target_self)}\001\e[0m\002)#{":#{nest_level}" unless nest_level.zero?}> "
  },
  proc { |target_self, nest_level, pry|
    "[#{pry.input_array.size}]\001\e[1;37m\002 #{Pry.config.prompt_name} #{RUBY_VERSION}\001\e[0m\002(\001\e[1;33m\002#{Pry.view_clip(target_self)}\001\e[0m\002)#{":#{nest_level}" unless nest_level.zero?}* "
  }
]
