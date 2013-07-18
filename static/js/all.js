function updateUserStatus(username) {
  $('.logged-out').hide();
  $('.logged-in .user .username').html(username);
  $('.logged-in').show();
}

$(function() {

    var Idea = Backbone.Model.extend({

        defaults: function() {
            return {
                title: "A great idea",
            };
        },

        url: function() {
            var origUrl = Backbone.Model.prototype.url.call(this);

            // add trailing slash to request url
            // necessary for Django as Backbone does not add trailing slash
            if (origUrl.substr(origUrl.length - 1) !== "/")
                origUrl += '/';
                
            return origUrl;
        },


        remove: function(event) {
            // wait: true makes sure Backbone waits for a response from the servere
            // before actually removing the model from the collection
            this.destroy({
                wait: true,
                error: function(result) {
                    $(event.currentTarget).closest('tr').find('td .linked').html('<strong>No permission to delete</strong>');
                    }
                });
        },

        initialize: function() {
            this.selected = false;
        },

    });

    var IdeaView = Backbone.View.extend({
        tagName: 'tr',

        template: _.template($('script#ideaRowTpl').html()),

        events: {
            "click": "toggleSelected",
            "click button#id_delete": "remove",
            "click .verify button.yes": "removeVerifyTrue",
            "click .verify button.no": "removeVerifyFalse"
        },

        remove: function(event) {
            event.stopImmediatePropagation();
            event.preventDefault();

            // replace button with verification stage buttons
            $(this.el).find('#id_delete').replaceWith($('script#verificationTpl').html());
        },

        removeVerifyTrue: function(event) {
            event.stopImmediatePropagation();
            event.preventDefault();
            this.model.remove(event);
        },

        removeVerifyFalse: function(event) {
            event.stopImmediatePropagation();
            event.preventDefault();
            this.render();
        },

        toggleSelected: function(event) {
            model = this.model;

            // switch 'selected' flag
            if (model.selected) {
                model.selected = false;
            } else {
                // deselect all other models
                model.collection.each(function(idea) {
                    idea.selected = false;
                });
                model.selected = true;
                // get neighbours
                this.getNeighbours();
            }

        },

        getNeighbours: function() {
            model = this.model;
            // deselect all other neighbours
            model.collection.each(function(idea) {
                idea.neighbour = false;
            });
            // get neighbours
            r = $.ajax({
                url: 'idea/' + this.model.id + '/neighbours/',
                type: 'GET',
                dataType: 'json',
                success: function(result) {
                    $.each(result, function(index, value) {
                        neighbour = model.collection.where(value)[0]
                        neighbour.neighbour = true;
                    });
                    // trigger change event on collection to rerender view
                    model.collection.trigger('change');
                }
            });
        },

        render: function() {
            self = this; // we need to reference the model from the inner scope of functions
            $(this.el).html(this.template(this.model.toJSON()));

            // make row drag- and droppable
            $(this.el).draggable({opacity: 0.5, distance: 20, helper: "clone"});
            $(this.el).droppable({
                hoverClass: "info",
                drop: function(event, ui) {
                    startNode = ui.draggable;
                    endNode = $(this);

                    startNodeID = startNode.find('td.idea-id').html();
                    endNodeID = endNode.find('td.idea-id').html();

                    $.ajax({
                        url: 'idea/' + startNodeID + '/neighbours/',
                        type: 'POST',
                        dataType: 'json',
                        data: {"neighbour": endNodeID * 1}, // convert from string to int, quite ugly
                        success: function(result) {
                            startNode.find('td .linked').html('<strong>Linked!</strong>').delay(500).animate({opacity: 0.0}, 800);
                            endNode.find('td .linked').html('<strong>Linked!</strong>').delay(500).animate({opacity: 0.0}, 800);
                            startNode.getNeighbours();
                        },
                    });
                },
            });

            // show selection by marking in green
            if (this.model.selected)
                $(this.el).addClass('success');

            if (this.model.neighbour)
                $(this.el).addClass('warning');

            return this;
        },
        
        initialize: function() {
            this.model.bind('error', function(a, b, c) {
                console.log(a, b, c);
            }, this);
        },

    });

    var IdeaCollection = Backbone.Collection.extend({
        model: Idea,
        url: 'http://localhost:8000/idea/',

    });

    var IdeaListView = Backbone.View.extend({
        tagName: 'tbody',

        initialize: function(options) {
            this.ideas = new IdeaCollection();

            this.ideas.bind('reset', this.render, this);
            this.ideas.bind('add', this.render, this);
            this.ideas.bind('change', this.render, this);
            this.ideas.bind('remove', this.render, this);
            this.ideas.fetch();
        },


        addOne: function(idea) {
            this.$el.append(new IdeaView({model: idea}).render().el);
            return this;
        },

        addNew: function(idea) {
            var self = this;
            this.ideas.create(idea, {wait: true, success: function(model, response){
                console.log(response);
                console.log(model);
            }});
            return this;
        },

        render: function() {
            this.$el.html('');
            this.ideas.each(this.addOne, this);
            return this;

        }
    });


    var AppView = Backbone.View.extend({
        el: '#app',

        events: {
            "click #ideaForm button#addButton": "handleSubmit",
            "click #loginModal button#loginButton": "handleLogin",
            "click a#logoutButton": "handleLogout",
            "keypress #ideaForm": "handleSubmitOnEnter",
        },

        updateUserStatus: function (username) {
          $('.logged-out').hide();
          $('.logged-in .user .username').html(username);
          $('.logged-in').show();
        },
        handleLogin: function(event) {
          event.preventDefault();
          event.stopImmediatePropagation();
          username = $('#loginModal #id_user').val();
          password = $('#loginModal #id_pass').val();

          Backbone.BasicAuth.set(username, password);

          r = $.ajax({
              url: 'loginStatus/',
              type: 'GET',
              dataType: 'json',
              success: function(result) {
                  if (waitingRequest) {
                    $.ajax(waitingRequest);
                    waitingRequest = null;
                  }
                  $('#loginModal').modal('hide');
                  updateUserStatus(username);
              },
              error: function(result) {
                  $('#loginModal .error').show();
              }
          });
        },

        handleLogout: function(event) {
            event.preventDefault();
            event.stopImmediatePropagation();
            Backbone.BasicAuth.clear();
            $.ajax( {
                url: 'logout/',
                type: 'POST',
            });
            $('.logged-in .user .username').html('');
            $('.logged-in').hide();
            $('.logged-out').show();
        },

        handleSubmit: function(event) {
            event.preventDefault();
            event.stopImmediatePropagation();
            var form = $('#ideaForm');

            var ideaData = {
                title: $(form).find('#id_title').val(),
            };

            this.ideaList.addNew(ideaData);

            return this;
        },

        handleSubmitOnEnter: function(event) {
            if (event.keyCode == 13) {
                return this.handleSubmit(event);
            }
        },

        initialize: function() {
            this.ideaList = new IdeaListView();
            this.loggedIn = false;
        },

        render: function() {
            this.$el.find('table').append(this.ideaList.render().el);
        },
    });

    var app = new AppView();
    app.render();

    waitingRequest = null;

    $.ajaxSetup({
        statusCode: {
            401: function(elm, xhr, s) {
                waitingRequest = this;
                $('#loginModal').modal('show');
            }
        }
    });

    $(document).ajaxSend(function(e, xhr, options) {
        var token = $.cookie('csrftoken');
        xhr.setRequestHeader('X-CSRFToken', token);
    });

    /* */

});
